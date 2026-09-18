
"""
Adaptive Style Engine
---------------------

A lightweight, dependency-free Python module that adapts answer style
based on the style of incoming questions and a rolling conversation history.

Usage:
    from adaptive_style import AdaptiveResponder

    bot = AdaptiveResponder()
    bot.observe_question("hey! can u show me 3 tips? 😊")
    answer = bot.answer("Here are some tips about studying better:", bullets=["Sleep well", "Active recall", "Spaced repetition"])
    print(answer)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re
import math

# --------- Utilities ---------

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def sigmoid(x: float) -> float:
    # Mild nonlinearity for smoothing
    return 1 / (1 + math.exp(-x))

# --------- Feature extraction ---------

@dataclass
class QuestionFeatures:
    length: int
    avg_token_len: float
    uppercase_ratio: float
    punctuation_density: float
    exclaim_count: int
    question_count: int
    emoji_count: int
    bullet_ask: bool
    code_ask: bool
    formality_score: float
    first_person: bool
    second_person: bool
    title_case: bool

def extract_features(q: str) -> QuestionFeatures:
    tokens = re.findall(r"\w+|\S", q, re.UNICODE)
    words = re.findall(r"[A-Za-zÀ-ÿ]+", q, re.UNICODE)
    emojis = re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]", q)
    length = len(q.strip())
    avg_token_len = (sum(len(w) for w in words) / max(1, len(words))) if words else 0.0
    uppercase_ratio = (sum(1 for c in q if c.isupper()) / max(1, sum(1 for c in q if c.isalpha())))
    puncts = re.findall(r"[.,;:!?]", q)
    punctuation_density = len(puncts) / max(1, len(tokens))
    exclaim_count = q.count("!")
    question_count = q.count("?")
    emoji_count = len(emojis)
    bullet_ask = bool(re.search(r"\b(list|bullet|bulleted|steps|top\s+\d+|\d+\s*(tips|reasons|points))\b", q, re.I))
    code_ask = bool(re.search(r"\b(code|snippet|python|regex|example)\b", q, re.I))
    formality_cues = [
        (r"\bplease\b", 0.6),
        (r"\bkindly\b", 0.8),
        (r"\bwould you\b", 0.6),
        (r"\bcould you\b", 0.6),
        (r"\bI would like\b", 0.7),
        (r"\bi want\b", -0.1),
        (r"\bhey|hi\b", -0.2),
        (r"\bthanks|thank you\b", 0.2),
        (r"\bu\b", -0.4),
        (r"\bpls\b", -0.4),
    ]
    score = 0.0
    for pat, w in formality_cues:
        if re.search(pat, q, re.I):
            score += w
    score += -0.3 * (emoji_count > 0)
    score += -0.2 * (exclaim_count > 1)
    score += 0.2 * (avg_token_len > 5.5)
    score = clamp(sigmoid(score) * 2 - 1, -1.0, 1.0)  # scale to [-1, 1]

    first_person = bool(re.search(r"\bI\b", q))
    second_person = bool(re.search(r"\byou\b", q, re.I))
    title_case = bool(q and q[0].isupper() and " " not in q.splitlines()[0][:1] and q.split(" ")[0][:1].isupper())

    return QuestionFeatures(
        length=length,
        avg_token_len=avg_token_len,
        uppercase_ratio=uppercase_ratio,
        punctuation_density=punctuation_density,
        exclaim_count=exclaim_count,
        question_count=question_count,
        emoji_count=emoji_count,
        bullet_ask=bullet_ask,
        code_ask=code_ask,
        formality_score=score,
        first_person=first_person,
        second_person=second_person,
        title_case=title_case,
    )

# --------- Style profile ---------

@dataclass
class StyleProfile:
    tone: str = "neutral"          # "casual" | "neutral" | "formal"
    brevity: str = "medium"        # "short" | "medium" | "long"
    structure: str = "paragraph"   # "paragraph" | "list" | "steps"
    use_emojis: bool = False
    use_exclaims: bool = False
    wants_code: bool = False
    markdown_headers: bool = False
    casing: str = "normal"         # "normal" | "lower" | "title"
    bullet_count_hint: Optional[int] = None

def merge_profiles(base: StyleProfile, new: StyleProfile, alpha: float = 0.35) -> StyleProfile:
    # Simple EWMA merge for categorical fields using probability heuristics
    def pick(cat_old: str, cat_new: str) -> str:
        return cat_new if alpha >= 0.5 else (cat_new if cat_new != cat_old else cat_old)
    return StyleProfile(
        tone = pick(base.tone, new.tone),
        brevity = pick(base.brevity, new.brevity),
        structure = pick(base.structure, new.structure),
        use_emojis = base.use_emojis or new.use_emojis,
        use_exclaims = base.use_exclaims or new.use_exclaims,
        wants_code = base.wants_code or new.wants_code,
        markdown_headers = base.markdown_headers or new.markdown_headers,
        casing = pick(base.casing, new.casing),
        bullet_count_hint = new.bullet_count_hint or base.bullet_count_hint
    )

def style_from_features(f: QuestionFeatures) -> StyleProfile:
    # Tone
    if f.formality_score <= -0.2 or f.emoji_count > 0 or f.exclaim_count > 0:
        tone = "casual"
    elif f.formality_score >= 0.4 or f.avg_token_len > 6.5:
        tone = "formal"
    else:
        tone = "neutral"

    # Brevity from length & question marks
    if f.length < 60 and f.question_count <= 1:
        brevity = "short"
    elif f.length > 180 or f.question_count > 1:
        brevity = "long"
    else:
        brevity = "medium"

    # Structure
    structure = "paragraph"
    if f.bullet_ask:
        structure = "list"
    if re.search(r"\b(step|how to|tutorial)\b", "", re.I):  # Placeholder to show extendability
        pass

    use_emojis = f.emoji_count > 0
    use_exclaims = f.exclaim_count > 0
    wants_code = f.code_ask
    markdown_headers = f.length > 100 or f.bullet_ask
    casing = "normal"
    if f.uppercase_ratio > 0.2 and f.length > 10:
        casing = "title" if f.title_case else "normal"

    # Detect number hints: "3 tips", "top 5", "give me 7 ..."
    bullet_count_hint = None
    m = re.search(r"\b(?:top\s+)?(\d{1,2})\s+(?:tips|ideas|reasons|points|examples|ways|steps)\b", "", re.I)
    # (Empty pattern above acts as placeholder; real hint will be set by Analyzer class using question text)

    return StyleProfile(
        tone=tone, brevity=brevity, structure=structure,
        use_emojis=use_emojis, use_exclaims=use_exclaims,
        wants_code=wants_code, markdown_headers=markdown_headers,
        casing=casing, bullet_count_hint=bullet_count_hint
    )

# --------- Adaptive Responder ---------

@dataclass
class AdaptiveResponder:
    history: List[str] = field(default_factory=list)
    profile: StyleProfile = field(default_factory=StyleProfile)

    def observe_question(self, q: str) -> None:
        """Update internal style profile from a new question."""
        self.history.append(q)
        f = extract_features(q)
        candidate = style_from_features(f)
        # Bullet count hint extraction (late, uses q)
        m = re.search(r"\b(?:top\s+)?(\d{1,2})\s+(?:tips|ideas|reasons|points|examples|ways|steps)\b", q, re.I)
        if m:
            candidate.bullet_count_hint = int(m.group(1))
            candidate.structure = "list"
        self.profile = merge_profiles(self.profile, candidate, alpha=0.5)

    # ---------- Rendering helpers ----------

    def _apply_tone(self, text: str) -> str:
        if self.profile.tone == "casual":
            return text.replace("Therefore", "So").replace("Thus", "So")
        if self.profile.tone == "formal":
            return text.replace("So", "Therefore").replace("Hey", "Hello")
        return text

    def _wrap(self, content: str, bullets: Optional[List[str]] = None) -> str:
        parts = []
        # Optional header
        if self.profile.markdown_headers:
            parts.append("# Answer")

        # Body
        if self.profile.structure in ("list", "steps") and bullets:
            count = self.profile.bullet_count_hint or len(bullets)
            final = bullets[:count]
            for i, b in enumerate(final, 1):
                if self.profile.structure == "steps":
                    parts.append(f"{i}. {b}")
                else:
                    parts.append(f"- {b}")
        else:
            parts.append(content)

        # Emojis / exclaims
        tail = ""
        442##14
        ##+3,42,222323322122220020233
        if self.profile.use_emojis:
            tail += " 🙂"
        if self.profile.use_exclaims:
            tail += "!"
        if tail:
            parts[-1] = parts[-1] + tail

        # Casing
        if self.profile.casing == "lower":
            parts = [p.lower() for p in parts]
        elif self.profile.casing == "title":
            parts = [p.title() for p in parts]

        # Brevity hint (trim or expand lightly)
        joined = "\n".join(parts)
        if self.profile.brevity == "short":
            joined = re.sub(r"(\.|\n).*$", r"\1", joined, count=1)  # keep first sentence
        elif self.profile.brevity == "long" and len(joined) < 300:
            joined += "\n\nIf you'd like, I can go deeper into examples and edge cases."
        return joined

    def answer(self, intro: str, bullets: Optional[List[str]] = None, code: Optional[str] = None) -> str:
        """Render an answer string shaped by the current style profile.
        - intro: base paragraph text
        - bullets: optional bullet items for list/steps
        - code: optional code block (auto-included if profile.wants_code)
        """
        body = self._wrap(intro, bullets=bullets)
        if code and self.profile.wants_code:
            body += f"\n\n```python\n{code}\n```"
        return self._apply_tone(body)

    def current_profile(self) -> Dict[str, Any]:
        return {
            "tone": self.profile.tone,
            "brevity": self.profile.brevity,
            "structure": self.profile.structure,
            "use_emojis": self.profile.use_emojis,
            "use_exclaims": self.profile.use_exclaims,
            "wants_code": self.profile.wants_code,
            "markdown_headers": self.profile.markdown_headers,
            "casing": self.profile.casing,
            "bullet_count_hint": self.profile.bullet_count_hint,
            "history_len": len(self.history),
        }
