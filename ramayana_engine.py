import os
import json
import numpy as np
from llama_index.core import StorageContext, load_index_from_storage, ServiceContext, set_global_service_context
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from custom_llm import OurLLM

BASE_DIR = os.environ.get("RAMAYAN_DATA_DIR", "/data")
KANDA_MAP = {
    1: "balakanda",
    2: "ayodhyakanda",
    3: "aranyakanda",
    4: "kishkindhakanda",
    5: "sundarakanda",
    6: "yuddhakanda",
    7: "uttarakanda",
}

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
set_global_service_context(
    ServiceContext.from_defaults(
        llm=OurLLM(), embed_model=embed_model,
        chunk_size=512, context_window=12000, num_output=512,
    )
)

with open(f"{BASE_DIR}/chunks/chunked_verses_may26.json", "r", encoding="utf-8") as f:
    verses = json.load(f)

RAG = load_index_from_storage(StorageContext.from_defaults(persist_dir=f"{BASE_DIR}/ramayana_512_index"))
kg_engines = {}


def _load_kg_engine(part, top_n):
    name = KANDA_MAP[part]
    idx = load_index_from_storage(StorageContext.from_defaults(persist_dir=f"{BASE_DIR}/KGs/{name}"))
    return idx.as_query_engine(
        include_text=True, embedding_mode="hybrid",
        similarity_top_k=top_n, max_knowledge_sequence=100, num_chunks_per_query=top_n,
    )


def _init_all_kg_engines(top_n):
    global kg_engines
    kg_engines = {part: _load_kg_engine(part, top_n) for part in KANDA_MAP}


_init_all_kg_engines(10)


def rerank_triplets(query, nodes, top_k=10):
    triplets = nodes[-1].metadata["kg_rel_texts"]
    if len(triplets) <= top_k:
        return triplets
    query_emb = np.array(embed_model.get_text_embedding(query))
    triplet_embs = np.array([embed_model.get_text_embedding(t) for t in triplets])
    scores = triplet_embs @ query_emb / (
        np.linalg.norm(triplet_embs, axis=1) * np.linalg.norm(query_emb)
    )
    return [triplets[i] for i in np.argsort(scores)[::-1][:top_k]]


def post_process(nodes, kg=True, part=1, query="", top_k=10):
    lol = {}
    data = ""

    if kg:
        data += f"{KANDA_MAP[part].upper()}\n\n"
        for node in nodes[:-1]:
            id_ = node.metadata["r_id"].split("_")[0]
            if id_ not in lol:
                lol[id_] = [node.metadata["canto_summary"]]
            lol[id_].append([node.text.replace("\n", ". "), f"{part}_{node.metadata['r_id']}"])

        for key, value in lol.items():
            if value[0] in ("No summary available", ""):
                value[0] = "empty"
            value[0] = value[0].replace("\n", ". ")
            data += f"{KANDA_MAP[part]} chapter {key} summary: {value[0]}\n"
            for i in value[1:]:
                data += f"{i[1]}: {i[0]}\n"
            data += "\n"
        data += "Following are the knowledge graph triplets used to retrieve above context:\n"
        for triplet in rerank_triplets(query, nodes, top_k):
            data += f"{triplet}\n"
    else:
        for node in nodes:
            parts = node.metadata["r_id"].split("_")
            id_ = f"{parts[0]}_{parts[1]}"
            if id_ not in lol:
                lol[id_] = [node.metadata["canto_summary"]]
            lol[id_].append([node.text, node.metadata["r_id"]])
        for key, value in lol.items():
            if value[0] in ("No summary available", ""):
                value[0] = "empty"
            value[0] = value[0].replace("\n", ". ")
            kp, ch = key.split("_")
            data += f"{KANDA_MAP[int(kp)]} chapter {ch} summary: {value[0]}\n"
            for i in value[1:]:
                data += f"{i[1]}: {i[0]}\n"
            data += "\n"
    return data


def get_ramayana_context(query, reinitialise=False, top_n_triplets=10, top_n_chunks=10):
    if reinitialise:
        _init_all_kg_engines(top_n_chunks)

    rag_engine = RAG.as_query_engine(similarity_top_k=top_n_chunks)
    rag_data = post_process(rag_engine.retrieve(query), False)

    all_data = ""
    for part in KANDA_MAP:
        nodes = kg_engines[part].retrieve(query)
        all_data += post_process(nodes, True, part, query, top_n_triplets)

    return all_data + "\nSome additional relevant information\n" + rag_data


def get_kanda_context(query, part, top_n_triplets=10, top_n_chunks=10):
    if part not in KANDA_MAP:
        return f"Invalid part {part}. Must be 1-7."
    engine = _load_kg_engine(part, top_n_chunks)
    nodes = engine.retrieve(query)
    return post_process(nodes, True, part, query, top_n_triplets)


def get_original_verses(part_chapter_chunk):
    if part_chapter_chunk in verses:
        return verses[part_chapter_chunk]
    return f"No verses found for '{part_chapter_chunk}'. Format: 'part_chapter_chunk' e.g. '1_12_3'."
