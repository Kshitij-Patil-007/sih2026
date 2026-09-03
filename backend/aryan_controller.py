from __future__ import annotations

from datetime import datetime, timezone

from backend.aryan_models import cdvqa, fusion, gemini, inhouse_vqa
from backend.aryan_preprocess import PreparedImage, to_data_url

CHANGE_HINTS = (
    "change",
    "before",
    "after",
    "difference",
    "damage",
    "flood",
    "inundat",
    "deforest",
    "new building",
    "destroyed",
    "compare",
    "delta",
)
CAPTION_HINTS = ("caption", "describe", "summarize", "what do you see", "scene description")
FUSION_HINTS = ("fusion", "fuse", "optical-sar", "optical sar", "sar and optical")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event(step: str, decision: str, detail: str) -> dict:
    return {"ts": _now(), "step": step, "decision": decision, "detail": detail}


def classify_intent(question: str, images: list[PreparedImage]) -> tuple[str, list[dict]]:
    events: list[dict] = []
    q = question.lower().strip()
    modalities = [im.modality for im in images]
    n = len(images)

    events.append(
        _event(
            "ingest",
            f"{n} image(s): " + ", ".join(f"{im.name}={im.modality}" for im in images),
            "Modality inferred from filename + pixel statistics after RGB composite.",
        )
    )

    if n == 2 and ("sar" in modalities and "optical" in modalities) and (
        any(h in q for h in FUSION_HINTS) or q == "" or "fuse" in q
    ):
        events.append(_event("intent", "optical_sar_fusion", "Paired optical + SAR with fusion phrasing."))
        return "optical_sar_fusion", events

    if n == 2 and (any(h in q for h in CHANGE_HINTS) or q.startswith("what changed")):
        events.append(
            _event(
                "intent",
                "change_vqa",
                "Two frames plus change-language → CDVQA (Aryan). Requires co-registered pair.",
            )
        )
        return "change_vqa", events

    if n == 2 and modalities.count("optical") == 2:
        events.append(
            _event(
                "intent",
                "change_vqa",
                "Two optical frames default to change detection even without explicit wording.",
            )
        )
        return "change_vqa", events

    if n == 2 and "sar" in modalities and "optical" in modalities:
        events.append(_event("intent", "optical_sar_fusion", "Heterogeneous pair routed to dual-encoder fusion."))
        return "optical_sar_fusion", events

    if any(h in q for h in CAPTION_HINTS):
        events.append(_event("intent", "caption", "Caption/describe language."))
        return "caption", events

    events.append(_event("intent", "vqa", "Single-image visual question answering."))
    return "vqa", events


def run_pipeline(question: str, images: list[PreparedImage]) -> dict:
    events: list[dict] = []
    for im in images:
        for note in im.notes:
            events.append(_event("preprocess", im.name, note))

    intent, extra = classify_intent(question, images)
    events.extend(extra)

    evidence: list[dict] = []
    model_used = ""
    extras: dict = {}
    fallback_used = False

    if intent == "change_vqa":
        if len(images) < 2:
            events.append(_event("gate", "reject_change", "Change detection needs 2 co-registered images."))
            answer = "Upload a before/after pair of the same area to run Change VQA."
            confidence = 0.2
            model_used = "gate"
        else:
            events.append(
                _event(
                    "model_select",
                    "cdvqa+gemini",
                    "Local CDVQA + Siamese patch head always run. Gemini v1 tried for optical RGB only.",
                )
            )
            local = cdvqa.run_cdvqa(images[0], images[1], question)
            extras = {
                "change_ratio": local["change_ratio"],
                "siamese_peak": local["siamese_peak"],
                "boxes": local["boxes"],
            }
            for note in local["notes"]:
                events.append(_event("cdvqa", "local_head", note))

            gemini_allowed = all(im.modality == "optical" for im in images)
            gemini_text = ""
            if not gemini_allowed:
                events.append(
                    _event(
                        "gemini_gate",
                        "blocked_sar",
                        "SAR is structurally unlike Gemini pretraining — local CDVQA only (challenge 01).",
                    )
                )
            else:
                prompt = (
                    "You are a remote-sensing change-detection analyst. "
                    "Image 1 is BEFORE, image 2 is AFTER. Answer the question concisely. "
                    "Cite visible evidence. If unsure, say so.\n\nQuestion: "
                    + question
                )
                g = gemini.generate(prompt, [images[0].rgb, images[1].rgb])
                if g.ok:
                    gemini_text = g.text
                    events.append(_event("gemini", "success", "Gemini v1 Change VQA completed."))
                else:
                    fallback_used = True
                    events.append(
                        _event(
                            "gemini",
                            "fallback",
                            g.error or "Gemini unavailable — venue-offline fallback is non-negotiable.",
                        )
                    )

            if gemini_text:
                answer = gemini_text + "\n\nLocal CDVQA cross-check: " + local["answer"]
                confidence = min(0.93, local["confidence"] + 0.08)
                model_used = "gemini-change-vqa + cdvqa"
            else:
                answer = local["answer"]
                confidence = local["confidence"]
                model_used = "cdvqa-local (Gemini fallback)"

            evidence.append(
                {
                    "title": "Change overlay (after + heatmap + Siamese boxes)",
                    "image": to_data_url(local["overlay"]),
                }
            )
            evidence.append({"title": "Before (aligned)", "image": to_data_url(local["before_aligned"])})
            evidence.append({"title": "After (aligned)", "image": to_data_url(local["after_aligned"])})

    elif intent == "optical_sar_fusion":
        optical = next((im for im in images if im.modality == "optical"), images[0])
        sar = next((im for im in images if im.modality == "sar"), images[-1])
        events.append(
            _event(
                "model_select",
                "inhouse_dual_encoder",
                "Optical–SAR fusion stays in-house. Gemini is not called on SAR.",
            )
        )
        fused = fusion.fuse(optical, sar)
        answer, confidence = fused["answer"], fused["confidence"]
        model_used = "optical-sar dual-encoder"
        extras = {"optical": optical.name, "sar": sar.name}
        for note in fused["notes"]:
            events.append(_event("fusion", "dual_encoder", note))
        evidence.append({"title": "Fusion visualization", "image": to_data_url(fused["overlay"])})

    elif intent == "caption":
        img = images[0]
        if img.modality == "sar":
            events.append(
                _event(
                    "gemini_gate",
                    "blocked_sar",
                    "Captioning is Gemini on optical RGB only. SAR caption → in-house VQA.",
                )
            )
            answer, confidence, extras = inhouse_vqa.answer_vqa(img, question or "describe the scene")
            model_used = "in-house LoRA VQA (SAR caption)"
            evidence.append({"title": "SAR RGB composite", "image": to_data_url(img.rgb)})
        else:
            events.append(_event("model_select", "gemini_caption", "Optical RGB captioning → Gemini."))
            prompt = (
                "Caption this remote-sensing optical RGB image in 2-3 sentences. "
                "Mention land cover, water, and built-up if visible. Question: "
                + (question or "Describe the scene.")
            )
            g = gemini.generate(prompt, [img.rgb])
            if g.ok:
                answer, confidence = g.text, 0.84
                model_used = "gemini-caption"
                events.append(_event("gemini", "success", "Optical caption from Gemini."))
            else:
                fallback_used = True
                answer, confidence = inhouse_vqa.caption_optical(img)
                model_used = "local-caption-fallback"
                events.append(_event("gemini", "fallback", g.error or "offline fallback caption"))
            evidence.append(
                {
                    "title": "False-color evidence",
                    "image": to_data_url(inhouse_vqa.overlay_class_map(img)),
                }
            )

    else:  # vqa
        img = images[0]
        events.append(
            _event(
                "model_select",
                "inhouse_lora_vqa",
                "Single-image VQA uses the in-house LoRA head (BigEarthNet classes). Full VLM fine-tune skipped.",
            )
        )
        answer, confidence, extras = inhouse_vqa.answer_vqa(img, question)
        model_used = "in-house LoRA VQA"
        if img.modality == "optical":
            g = gemini.generate(
                "Answer this remote-sensing question briefly.\nQuestion: " + question,
                [img.rgb],
            )
            if g.ok:
                answer = g.text + "\n\nLoRA class head: " + answer
                confidence = min(0.92, confidence + 0.07)
                model_used = "gemini + in-house LoRA VQA"
                events.append(_event("gemini", "success", "Gemini supplement on optical VQA."))
            else:
                fallback_used = True
                events.append(_event("gemini", "fallback", g.error or "offline — LoRA head only"))
        else:
            events.append(_event("gemini_gate", "blocked_sar", "SAR VQA stays on the in-house model."))
        evidence.append(
            {
                "title": "Input RGB composite",
                "image": to_data_url(img.rgb),
            }
        )

    events.append(
        _event(
            "merge",
            "compose_answer",
            f"model={model_used}; confidence={confidence:.2f}; fallback={fallback_used}",
        )
    )

    return {
        "intent": intent,
        "answer": answer,
        "confidence": round(float(confidence), 3),
        "model_used": model_used,
        "fallback_used": fallback_used,
        "evidence": evidence,
        "extras": extras,
        "audit": events,
    }
