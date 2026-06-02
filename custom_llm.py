from typing import Any
from llama_index.core.llms import CustomLLM, CompletionResponse, CompletionResponseGen, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
    "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for", "with",
    "about", "against", "between", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s",
    "t", "can", "will", "just", "don", "should", "now", "also", "could", "would",
    "shall", "may", "might", "must", "need", "let", "got", "get", "go", "gone",
    "went", "come", "came", "take", "taken", "took", "make", "made", "give", "gave",
    "given", "say", "said", "tell", "told", "know", "known", "knew", "think",
    "thought", "see", "seen", "saw", "want", "like", "well", "back", "even", "still",
    "way", "many", "much", "every", "another", "around", "since", "into", "upon",
    "already", "yet", "always", "never", "often", "ever", "however", "therefore",
    "thus", "hence", "although", "though", "whether", "rather", "quite", "enough",
    "almost", "really", "perhaps", "please", "yes", "no", "ok", "okay", "dear",
    "sure", "anyway", "besides", "else", "instead", "along", "across", "among",
    "towards", "within", "without", "near", "far", "away", "behind", "beside",
    "beyond", "despite", "except", "regarding", "according", "per", "via", "unto",
    "whereas", "whereby", "wherein", "wherever", "whenever", "whoever", "whatever",
    "whichever", "been", "being", "become", "became", "seem", "seemed", "keep",
    "kept", "put", "set", "run", "turn", "show", "shown", "use", "used", "using",
    "ask", "asked", "called", "call",
}

def _extract_keywords(text):
    words = text.lower().split()
    keywords = [w.strip(".,!?;:\"'()[]{}") for w in words]
    keywords = [w for w in keywords if w and w not in STOP_WORDS and len(w) > 1]
    return list(dict.fromkeys(keywords))


class OurLLM(CustomLLM):
    context_window: int = 20000
    num_output: int = 512
    model_name: str = "custom"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        try:
            pp = prompt.split("---------\n")[1].split("\n-----------")[0]
        except Exception:
            pp = prompt
        return CompletionResponse(text=", ".join(_extract_keywords(pp)))

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        raise NotImplementedError()
