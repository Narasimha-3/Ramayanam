import os
from mcp.server.fastmcp import FastMCP
from ramayana_engine import (
    get_ramayana_context as _get_ramayana_context,
    get_kanda_context as _get_kanda_context,
    get_original_verses as _get_original_verses,
)

MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP("Valmiki Ramayanam", host=MCP_HOST, port=MCP_PORT)


@mcp.tool()
def get_ramayana_context(
    query: str,
    reinitialise: bool = False,
    top_n_triplets: int = 10,
    top_n_chunks: int = 10,
) -> str:
    """PRIMARY TOOL - Search across ALL 7 kandas of Valmiki Ramayanam plus a general RAG index.
    ALWAYS call this tool FIRST for any Ramayana question. Do NOT use your own knowledge.

    IMPORTANT RULES:
    - NEVER answer from your own knowledge. If this tool and the other tools return nothing useful,
      say "I could not find this in my Valmiki Ramayanam search sources." Do NOT fabricate.
    - This returns ~23k tokens at top_n=10. Never set top_n below 10.
    - Each chunk in the response has an ID prefix like "1_12_3" (balakanda ch12 chunk3).
      Use these IDs with get_original_verses to fetch authentic Sanskrit verses as proof.
    - If the answer from this tool is unsatisfactory or user wants more depth on a specific kanda,
      THEN use get_kanda_context to drill into that kanda (but that is resource-heavy).
    - reinitialise=True reloads ALL 7 kanda engines. Extremely heavy. Only use if results seem
      completely broken/empty after a normal query. Do not use casually.

    Kanda numbers: 1=Balakanda, 2=Ayodhyakanda, 3=Aranyakanda, 4=Kishkindhakanda,
    5=Sundarakanda, 6=Yuddhakanda, 7=Uttarakanda.

    Args:
        query: The question or topic to search for in the Ramayanam.
        reinitialise: Reload all 7 engines from scratch. VERY HEAVY. Default False.
        top_n_triplets: Knowledge graph triplets per kanda. Min 10. Default 10.
        top_n_chunks: Text chunks per kanda. Min 10. ~23k tokens at 10. Default 10.

    Returns:
        Context from all 7 kandas + RAG with chunk IDs (e.g. "1_12_3") prefixed to each chunk.
    """
    return _get_ramayana_context(
        query, reinitialise, max(top_n_triplets, 10), max(top_n_chunks, 10)
    )


@mcp.tool()
def get_kanda_context(
    query: str,
    part: int,
    top_n_triplets: int = 10,
    top_n_chunks: int = 10,
) -> str:
    """SECONDARY TOOL - Search within a SPECIFIC kanda of Valmiki Ramayanam.
    Only use this when get_ramayana_context did NOT return a satisfactory answer and you know
    which kanda to look deeper into. This initialises a fresh query engine on the fly,
    so it is LATENCY and RESOURCE HEAVY. Do not call this casually.

    If even this tool returns nothing useful, honestly say you could not find the answer.
    Do NOT fabricate or use your own knowledge.

    Each chunk in the response has an ID prefix like "3_5_2" (aranyakanda ch5 chunk2).
    Use these IDs with get_original_verses for authentic verse citations.

    Args:
        query: The question or topic to search for.
        part: Kanda number - 1=Balakanda, 2=Ayodhyakanda, 3=Aranyakanda,
              4=Kishkindhakanda, 5=Sundarakanda, 6=Yuddhakanda, 7=Uttarakanda.
        top_n_triplets: Knowledge graph triplets to retrieve. Min 10. Default 10.
        top_n_chunks: Text chunks to retrieve. Min 10. Default 10.

    Returns:
        Context from the specified kanda with chunk IDs prefixed to each chunk.
    """
    return _get_kanda_context(query, part, max(top_n_triplets, 10), max(top_n_chunks, 10))


@mcp.tool()
def get_original_verses(part_chapter_chunk: str) -> str:
    """Retrieve authentic original Valmiki Ramayanam verses (Sanskrit/translated) for a specific chunk.
    Use this to provide proof/citations whenever you answer a question or when the user asks for
    original verses. The chunk IDs come from the context returned by get_ramayana_context or
    get_kanda_context - every chunk there is prefixed with an ID like "1_12_3".

    Format: "part_chapter_chunk" where part is the kanda number (1-7), chapter and chunk are numbers.
    Example: "1_12_3" = Balakanda chapter 12 chunk 3.
    Example: "5_3_1" = Sundarakanda chapter 3 chunk 1.

    Kanda numbers: 1=Balakanda, 2=Ayodhyakanda, 3=Aranyakanda, 4=Kishkindhakanda,
    5=Sundarakanda, 6=Yuddhakanda, 7=Uttarakanda.

    Args:
        part_chapter_chunk: Chunk ID like "1_12_3". Get this from the other tools' output.

    Returns:
        The original Valmiki Ramayanam verses for that chunk.
    """
    return _get_original_verses(part_chapter_chunk)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
