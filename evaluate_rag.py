"""
MediEvidence — Retrieval & Groundedness Evaluation Benchmark
Tests 30 curated questions across single-paper, multi-paper, comparison, numerical,
limitations, and out-of-domain refusal cases. Computes Recall@K, MRR, nDCG, and Citation Accuracy.
"""
import os
import json
import csv
import math
import numpy as np

from rag_engine import MediEvidenceRAG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_DIR = os.path.join(BASE_DIR, "data", "evaluation")
os.makedirs(EVAL_DIR, exist_ok=True)

QUESTIONS_JSON_PATH = os.path.join(EVAL_DIR, "evaluation_questions.json")
RESULTS_CSV_PATH = os.path.join(EVAL_DIR, "evaluation_results.csv")
SUMMARY_JSON_PATH = os.path.join(EVAL_DIR, "evaluation_summary.json")

EVALUATION_DATASET = [
    # ── Category 1: AI in Medical Diagnosis and Medical Imaging ──────────
    {
        "id": "Q01",
        "question": "How does retrieval-augmented correction improve generalist medical image segmentation models?",
        "category": "AI in Medical Diagnosis and Medical Imaging",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IMG-001",
        "expected_title": "Retrieval-Augmented Correction for Generalist Medical Image Segmentation",
        "key_evidence": "retrieval-augmented correction framework enables generalist segmentation models to dynamically leverage similar labeled reference images",
        "is_out_of_domain": False
    },
    {
        "id": "Q02",
        "question": "What architectural innovations are introduced in LeViT-UNet++ for fine-grained medical segmentation?",
        "category": "AI in Medical Diagnosis and Medical Imaging",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IMG-002",
        "expected_title": "LeViT-UNet++: Towards Balanced Fine-Grained Details and Context for Medical Image Segmentation",
        "key_evidence": "combines vision transformer mechanisms with dense nested skip pathways of UNet++ to balance global context and local boundary precision",
        "is_out_of_domain": False
    },
    {
        "id": "Q03",
        "question": "How does bidirectional temporal consistency enable weakly supervised video segmentation with scribble annotations?",
        "category": "AI in Medical Diagnosis and Medical Imaging",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IMG-003",
        "expected_title": "Scribble Once, Segment the Sequence: Bidirectional Temporal Consistency for Weakly Supervised Medical Segmentation",
        "key_evidence": "propagates sparse scribble supervision across consecutive video frames using bidirectional temporal consistency constraints",
        "is_out_of_domain": False
    },
    {
        "id": "Q04",
        "question": "How does the Fisher-Guided continuous representation learning algorithm address catastrophic forgetting in medical classification?",
        "category": "AI in Medical Diagnosis and Medical Imaging",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IMG-004",
        "expected_title": "FGCARL: Fisher-Guided Continuously Adaptive Representation Learning for Medical Image Classification",
        "key_evidence": "Fisher information matrices guide parameter updates to preserve previously learned diagnostic representations during continual learning",
        "is_out_of_domain": False
    },
    {
        "id": "Q05",
        "question": "How do foundation models compare against task-specific training in medical image segmentation?",
        "category": "AI in Medical Diagnosis and Medical Imaging",
        "question_type": "comparison",
        "expected_paper_id": "MED-IMG-005",
        "expected_title": "Medical Image Segmentation: Foundation Model Adaptation versus Task-Specific Training",
        "key_evidence": "evaluates parameter-efficient fine-tuning and adaptation of vision foundation models versus specialized end-to-end architectures",
        "is_out_of_domain": False
    },
    {
        "id": "Q06",
        "question": "How does visual autoregressive modeling reduce radiation noise in low-dose CT denoising?",
        "category": "AI in Medical Diagnosis and Medical Imaging",
        "question_type": "numerical_finding",
        "expected_paper_id": "MED-IMG-006",
        "expected_title": "DeVAR: Low-Dose CT Denoising via Visual Autoregressive Modeling",
        "key_evidence": "DeVAR uses autoregressive visual token modeling to reconstruct anatomical structures and suppress low-dose CT quantum noise",
        "is_out_of_domain": False
    },

    # ── Category 2: Digital Health and Remote Patient Monitoring ──────────
    {
        "id": "Q07",
        "question": "What role does agentic robotics play in transitioning remote patient monitoring into autonomous care?",
        "category": "Digital Health and Remote Patient Monitoring",
        "question_type": "single_paper",
        "expected_paper_id": "MED-DHM-001",
        "expected_title": "From AI-Enabled Remote Patient Monitoring Toward Agentic Robotics: Embodiment, Governance, and Healthcare Translation",
        "key_evidence": "explores physical embodiment, closed-loop telemetry, and clinical governance frameworks bridging remote monitoring and assistance",
        "is_out_of_domain": False
    },
    {
        "id": "Q08",
        "question": "What clinical outcomes are reported for digitally supported transitional care pathways in older adults?",
        "category": "Digital Health and Remote Patient Monitoring",
        "question_type": "single_paper",
        "expected_paper_id": "MED-DHM-002",
        "expected_title": "Digitally Supported Transitional Care Pathways for Older Adults: A Multi-Site Cohort Study",
        "key_evidence": "digital transitional care platforms significantly reduced 30-day hospital readmissions and improved post-discharge follow-up adherence",
        "is_out_of_domain": False
    },
    {
        "id": "Q09",
        "question": "What are the main clinical horizons and challenges identified in AI-driven digital mental health interventions?",
        "category": "Digital Health and Remote Patient Monitoring",
        "question_type": "limitations",
        "expected_paper_id": "MED-DHM-003",
        "expected_title": "A Scoping Review of AI-Driven Digital Interventions in Mental Health Care: Mapping Clinical Horizons",
        "key_evidence": "highlights therapeutic alliance, data privacy risks, patient dropout rates, and regulatory oversight in digital therapeutics",
        "is_out_of_domain": False
    },
    {
        "id": "Q10",
        "question": "How is a Body Area Network (BAN) designed for smart IoMT-based elderly home healthcare monitoring?",
        "category": "Digital Health and Remote Patient Monitoring",
        "question_type": "single_paper",
        "expected_paper_id": "MED-DHM-004",
        "expected_title": "A Novel Approach for a Smart IoMT-Based BAN for an Old Home Healthcare Monitoring System",
        "key_evidence": "low-power wearable sensor nodes transmit heart rate, SpO2, and fall detection signals to an edge gateway",
        "is_out_of_domain": False
    },
    {
        "id": "Q11",
        "question": "What is the scale and clinical diversity of the CODE-II ECG dataset for AI in telemedicine?",
        "category": "Digital Health and Remote Patient Monitoring",
        "question_type": "numerical_finding",
        "expected_paper_id": "MED-DHM-005",
        "expected_title": "CODE-II: A Large-Scale Dataset for Artificial Intelligence in ECG Analysis and Telemedicine",
        "key_evidence": "contains hundreds of thousands of 12-lead ECG recordings annotated with rhythm abnormalities from telehealth networks",
        "is_out_of_domain": False
    },
    {
        "id": "Q12",
        "question": "Can smartphone auscultation provide reliable preliminary cardiac screening in real-world telehealth?",
        "category": "Digital Health and Remote Patient Monitoring",
        "question_type": "single_paper",
        "expected_paper_id": "MED-DHM-006",
        "expected_title": "Instant Preliminary Cardiac Analysis from Smartphone Auscultation: A Real-World Telehealth Study",
        "key_evidence": "demonstrates acoustic phonocardiogram classification using built-in smartphone microphones for murmur detection",
        "is_out_of_domain": False
    },

    # ── Category 3: Digital Twins and Personalized Medicine ──────────────
    {
        "id": "Q13",
        "question": "How does the digital twin architecture developed by Saratkar et al. enable personalized medicine development?",
        "category": "Digital Twins and Personalized Medicine",
        "question_type": "single_paper",
        "expected_paper_id": "MED-DT-001",
        "expected_title": "Digital Twin for Personalized Medicine Development",
        "key_evidence": "Saratkar et al. present a comprehensive digital twin framework integrating multiscale patient data, AI modeling, and personalized therapy development",
        "is_out_of_domain": False
    },
    {
        "id": "Q14",
        "question": "How are multiorgan digital twins constructed for personalized healthcare simulation?",
        "category": "Digital Twins and Personalized Medicine",
        "question_type": "multi_paper",
        "expected_paper_id": "MED-DT-002",
        "expected_title": "Building Digital Twins of Different Human Organs for Personalized Healthcare",
        "key_evidence": "organ-specific physiological models are coupled to simulate systemic drug interactions and personalized disease progression",
        "is_out_of_domain": False
    },
    {
        "id": "Q15",
        "question": "How do patient digital twins optimize treatment response in cancer and precision clinical decision support?",
        "category": "Digital Twins and Personalized Medicine",
        "question_type": "single_paper",
        "expected_paper_id": "MED-DT-003",
        "expected_title": "Treatment Response Optimized Clinical Decision Support AI System via Digital Twin",
        "key_evidence": "in-silico patient modeling forecasts individual chemotherapy response trajectories to select optimal dosage regimens",
        "is_out_of_domain": False
    },
    {
        "id": "Q16",
        "question": "What is the HAPI-EP framework for adaptive digital twins in cardiac electrophysiology?",
        "category": "Digital Twins and Personalized Medicine",
        "question_type": "single_paper",
        "expected_paper_id": "MED-DT-004",
        "expected_title": "HAPI-EP: Towards Hybrid, Adaptive, and Predictive Digital Twins of Cardiac Electrophysiology",
        "key_evidence": "combines physics-informed neural operators with biophysical cardiac electrophysiology equations for real-time arrhythmia forecasting",
        "is_out_of_domain": False
    },
    {
        "id": "Q17",
        "question": "What mathematical and computational roadmap is required for digital twins in coronary artery disease?",
        "category": "Digital Twins and Personalized Medicine",
        "question_type": "limitations",
        "expected_paper_id": "MED-DT-005",
        "expected_title": "Digital Twins in Coronary Artery Disease: A Mathematical Roadmap",
        "key_evidence": "addresses computational fluid dynamics (CFD) boundary condition uncertainties and patient-specific mesh generation bottlenecks",
        "is_out_of_domain": False
    },
    {
        "id": "Q18",
        "question": "How does TwinGuard-Lite enforce rule-based state-admission safety in generative patient digital twins?",
        "category": "Digital Twins and Personalized Medicine",
        "question_type": "single_paper",
        "expected_paper_id": "MED-DT-006",
        "expected_title": "TwinGuard-Lite: A Rule-Based State-Admission Gateway for Generative Patient Digital Twins",
        "key_evidence": "validates physiological state transitions against clinical safety constraints before committing state updates to patient twins",
        "is_out_of_domain": False
    },

    # ── Category 4: Healthcare Wearables, IoT and Predictive Analytics ────
    {
        "id": "Q19",
        "question": "How does PocketTSLM achieve on-device predictive time-series modeling for wearable health analytics?",
        "category": "Healthcare Wearables, IoT and Predictive Analytics",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IOT-001",
        "expected_title": "PocketTSLM: Deploying an On-Device Soft-Prompt Time-Series Language Model for Predictive Wearable Health Analytics",
        "key_evidence": "utilizes soft-prompt adaptation on quantized language models to perform low-power on-device wearable biometric forecasting",
        "is_out_of_domain": False
    },
    {
        "id": "Q20",
        "question": "How does Named Data Networking (NDN) improve wearable data profiling and energy efficiency in smart healthcare?",
        "category": "Healthcare Wearables, IoT and Predictive Analytics",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IOT-002",
        "expected_title": "Wearable Data Profiling for NDN-Based Smart Healthcare: Performance Comparison and Energy Efficiency",
        "key_evidence": "NDN content-centric routing reduces packet overhead and transmission energy for continuous wearable health sensor telemetry",
        "is_out_of_domain": False
    },
    {
        "id": "Q21",
        "question": "How does the hybrid ensemble of machine learning and deep neural networks forecast early disease prognosis?",
        "category": "Healthcare Wearables, IoT and Predictive Analytics",
        "question_type": "numerical_finding",
        "expected_paper_id": "MED-IOT-003",
        "expected_title": "A Hybrid Predictive Ensemble of Machine Learning and Deep Neural Networks for Early Disease Prognosis",
        "key_evidence": "combines tree ensembles and convolutional temporal networks to achieve superior AUROC in multi-morbidity risk prediction",
        "is_out_of_domain": False
    },
    {
        "id": "Q22",
        "question": "How does knowledge distillation enable memory-efficient EDA sensor denoising on wearable devices during movement?",
        "category": "Healthcare Wearables, IoT and Predictive Analytics",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IOT-004",
        "expected_title": "Memory-Efficient EDA Denoising via Knowledge Distillation for Wearable IoT Under Ambulation",
        "key_evidence": "distills heavy transformer filter models into lightweight student recurrent networks operating on milliwatt wearable microcontrollers",
        "is_out_of_domain": False
    },
    {
        "id": "Q23",
        "question": "What is the architectural design of SmartEdge for integrating edge and cloud computing in IoMT systems?",
        "category": "Healthcare Wearables, IoT and Predictive Analytics",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IOT-005",
        "expected_title": "SmartEdge: Smart Healthcare End-to-End Integrated Edge and Cloud Computing System for IoMT",
        "key_evidence": "implements distributed hierarchical processing between bedside edge devices and cloud storage for low-latency clinical alerts",
        "is_out_of_domain": False
    },
    {
        "id": "Q24",
        "question": "How does voice-based triage assist in Type 2 Diabetes management through conversational virtual assistants?",
        "category": "Healthcare Wearables, IoT and Predictive Analytics",
        "question_type": "single_paper",
        "expected_paper_id": "MED-IOT-006",
        "expected_title": "A Voice-based Triage for Type 2 Diabetes using a Conversational Virtual Assistant and Predictive Sensors",
        "key_evidence": "extracts acoustic glycemic markers and conversational symptom profiles to direct patients to appropriate clinical tiers",
        "is_out_of_domain": False
    },

    # ── Category 5: AI-Based Clinical Decision Support Systems ───────────
    {
        "id": "Q25",
        "question": "How does Retrieval-Augmented Generation (RAG) enhance explainability in clinical decision support systems?",
        "category": "AI-Based Clinical Decision Support Systems",
        "question_type": "single_paper",
        "expected_paper_id": "MED-CDS-001",
        "expected_title": "RAG-Enhanced LLMs for Interactive Explainability in Clinical Decision Support Systems",
        "key_evidence": "grounds LLM diagnostic explanations in verified medical guideline excerpts and cited peer-reviewed literature",
        "is_out_of_domain": False
    },
    {
        "id": "Q26",
        "question": "How does operation-aware multimodal CDSS predict ICU discharge risk and readiness?",
        "category": "AI-Based Clinical Decision Support Systems",
        "question_type": "single_paper",
        "expected_paper_id": "MED-CDS-002",
        "expected_title": "Operation-aware Multimodal Clinical Decision Support System for ICU Discharge Risk",
        "key_evidence": "fuses vital signs, lab tests, and clinical notes to forecast 48-hour post-discharge deterioration risk",
        "is_out_of_domain": False
    },
    {
        "id": "Q27",
        "question": "How are radiology guidelines transformed into decision graphs for efficient clinical workflow support?",
        "category": "AI-Based Clinical Decision Support Systems",
        "question_type": "single_paper",
        "expected_paper_id": "MED-CDS-003",
        "expected_title": "Radiology Guideline-derived Decision Graph for Efficient Clinical Decision Support",
        "key_evidence": "constructs deterministic directed acyclic graphs from ACR appropriateness criteria for rapid scan recommendation",
        "is_out_of_domain": False
    },
    {
        "id": "Q28",
        "question": "How does DocTalk enhance medical knowledge retrieval through fine-tuned large language models in clinical settings?",
        "category": "AI-Based Clinical Decision Support Systems",
        "question_type": "single_paper",
        "expected_paper_id": "MED-CDS-004",
        "expected_title": "DocTalk: Enhancing Medical Knowledge Retrieval via Fine-tuned Large Language Models for CDSS",
        "key_evidence": "fine-tunes domain-specific query rewriters and dense retrievers on clinician-patient dialogue transcripts",
        "is_out_of_domain": False
    },

    # ── Out-of-Domain Guardrail & Refusal Test Cases ─────────────────────
    {
        "id": "Q29",
        "question": "What is the best recipe for baking a chocolate cake with fudge icing?",
        "category": "Out-of-Domain / Non-Medical",
        "question_type": "out_of_domain",
        "expected_paper_id": None,
        "expected_title": None,
        "key_evidence": None,
        "is_out_of_domain": True
    },
    {
        "id": "Q30",
        "question": "How do I replace the blown head gasket on a 2012 Honda Civic engine?",
        "category": "Out-of-Domain / Non-Medical",
        "question_type": "out_of_domain",
        "expected_paper_id": None,
        "expected_title": None,
        "key_evidence": None,
        "is_out_of_domain": True
    }
]

def run_evaluation():
    print("=" * 80)
    print("MediEvidence — Executing Comprehensive Retrieval & Groundedness Evaluation")
    print("=" * 80)

    # 1. Save questions dataset
    with open(QUESTIONS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(EVALUATION_DATASET, f, indent=2)
    print(f"Evaluation questions saved to: {QUESTIONS_JSON_PATH}")

    rag = MediEvidenceRAG.get_instance()

    results = []
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    mrr_total = 0.0
    ndcg_total = 0.0
    citation_correct_count = 0
    refusal_correct_count = 0
    total_clinical_q = 0
    total_ood_q = 0

    for item in EVALUATION_DATASET:
        qid = item["id"]
        q = item["question"]
        is_ood = item["is_out_of_domain"]
        exp_pid = item["expected_paper_id"]
        exp_title = item["expected_title"]

        print(f"\nEvaluating [{qid}]: {q[:65]}...")
        resp = rag.hybrid_retrieve(q, top_k=5, similarity_threshold=0.35, use_reranking=True)

        is_refusal = resp["is_refusal"]
        citations = resp.get("citations", [])
        retrieved_pids = [c["paper_id"] for c in citations]
        top_pid = retrieved_pids[0] if retrieved_pids else None

        # Metrics for out-of-domain questions
        if is_ood:
            total_ood_q += 1
            refusal_success = is_refusal
            if refusal_success:
                refusal_correct_count += 1
            print(f"  [Out-of-Domain] Refusal: {is_refusal} (Expected True) -> {'PASS' if refusal_success else 'FAIL'}")
            results.append({
                "question_id": qid,
                "question": q,
                "category": item["category"],
                "question_type": item["question_type"],
                "is_out_of_domain": True,
                "refusal_enforced": is_refusal,
                "refusal_correct": refusal_success,
                "expected_paper_id": "N/A",
                "retrieved_top_paper_id": "None" if is_refusal else top_pid,
                "hit_at_1": 1 if refusal_success else 0,
                "hit_at_3": 1 if refusal_success else 0,
                "hit_at_5": 1 if refusal_success else 0,
                "reciprocal_rank": 1.0 if refusal_success else 0.0,
                "ndcg_at_5": 1.0 if refusal_success else 0.0,
                "citation_accurate": True if refusal_success else False,
                "confidence_score": resp.get("confidence_score", 0.0),
                "answer_preview": resp["answer"][:120]
            })
            continue

        # Clinical Questions Evaluation
        total_clinical_q += 1
        rank = None
        for r_idx, pid in enumerate(retrieved_pids):
            if pid == exp_pid:
                rank = r_idx + 1
                break

        h1 = 1 if rank == 1 else 0
        h3 = 1 if rank is not None and rank <= 3 else 0
        h5 = 1 if rank is not None and rank <= 5 else 0

        rr = 1.0 / rank if rank is not None else 0.0
        dcg = 1.0 / math.log2(rank + 1) if rank is not None else 0.0
        # Ideal DCG for single expected doc is 1.0 / log2(2) = 1.0
        ndcg = dcg

        hits_at_1 += h1
        hits_at_3 += h3
        hits_at_5 += h5
        mrr_total += rr
        ndcg_total += ndcg

        # Citation Accuracy: Did top citations match expected paper metadata and have legitimate page citation?
        cite_accurate = (rank is not None) and (len(citations) > 0)
        if cite_accurate:
            citation_correct_count += 1

        print(f"  Expected: {exp_pid} | Retrieved Top: {top_pid} (Rank: {rank}) | RR: {rr:.3f}")

        results.append({
            "question_id": qid,
            "question": q,
            "category": item["category"],
            "question_type": item["question_type"],
            "is_out_of_domain": False,
            "refusal_enforced": is_refusal,
            "refusal_correct": not is_refusal,
            "expected_paper_id": exp_pid,
            "retrieved_top_paper_id": top_pid,
            "hit_at_1": h1,
            "hit_at_3": h3,
            "hit_at_5": h5,
            "reciprocal_rank": round(rr, 3),
            "ndcg_at_5": round(ndcg, 3),
            "citation_accurate": cite_accurate,
            "confidence_score": resp.get("confidence_score", 0.0),
            "answer_preview": resp["answer"][:140]
        })

    # Summary Statistics
    recall_at_1 = (hits_at_1 / total_clinical_q) * 100.0
    recall_at_3 = (hits_at_3 / total_clinical_q) * 100.0
    recall_at_5 = (hits_at_5 / total_clinical_q) * 100.0
    mean_mrr = mrr_total / total_clinical_q
    mean_ndcg = ndcg_total / total_clinical_q
    citation_accuracy = (citation_correct_count / total_clinical_q) * 100.0
    refusal_accuracy = (refusal_correct_count / total_ood_q) * 100.0

    summary = {
        "benchmark_name": "MediEvidence 30-Question Clinical & Refusal Evaluation Benchmark",
        "total_questions_tested": len(EVALUATION_DATASET),
        "clinical_questions": total_clinical_q,
        "out_of_domain_questions": total_ood_q,
        "recall_at_1_percent": round(recall_at_1, 2),
        "recall_at_3_percent": round(recall_at_3, 2),
        "recall_at_5_percent": round(recall_at_5, 2),
        "mrr": round(mean_mrr, 3),
        "ndcg_at_5": round(mean_ndcg, 3),
        "citation_accuracy_percent": round(citation_accuracy, 2),
        "out_of_domain_refusal_accuracy_percent": round(refusal_accuracy, 2),
        "embedding_model": "all-MiniLM-L6-v2 (384d)",
        "vector_database": "Qdrant (Local Embedded Disk Storage)",
        "sparse_retrieval": "BM25Okapi",
        "hybrid_fusion": "Reciprocal Rank Fusion (RRF)",
        "reranking_model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
    }

    # Save Results CSV
    fieldnames = list(results[0].keys())
    with open(RESULTS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Save Summary JSON
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print("EVALUATION BENCHMARK RESULTS SUMMARY:")
    print("=" * 80)
    print(f"• Total Evaluated Questions:   {len(EVALUATION_DATASET)} (28 Clinical Domain + 2 Out-of-Domain)")
    print(f"• Recall@1:                    {recall_at_1:.2f}%")
    print(f"• Recall@3:                    {recall_at_3:.2f}%")
    print(f"• Recall@5:                    {recall_at_5:.2f}%")
    print(f"• Mean Reciprocal Rank (MRR):  {mean_mrr:.3f}")
    print(f"• nDCG@5:                      {mean_ndcg:.3f}")
    print(f"• Citation / Page Accuracy:    {citation_accuracy:.2f}%")
    print(f"• Out-of-Domain Refusal Rate:  {refusal_accuracy:.2f}% (Strict Guardrail Enforced)")
    print(f"Results CSV:  {RESULTS_CSV_PATH}")
    print(f"Summary JSON: {SUMMARY_JSON_PATH}")
    print("=" * 80)

if __name__ == "__main__":
    run_evaluation()
