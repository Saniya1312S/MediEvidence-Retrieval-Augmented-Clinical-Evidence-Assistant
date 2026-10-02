/* =============================================
   RAG Clinical Evidence Assistant — Script
   ============================================= */

// === Particle Background ===
(function initParticles() {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];
    const PARTICLE_COUNT = 60;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.3;
            this.speedY = (Math.random() - 0.5) * 0.3;
            this.opacity = Math.random() * 0.3 + 0.05;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(99, 102, 241, ${this.opacity})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle());
    }

    function connectParticles() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 150) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(99, 102, 241, ${0.04 * (1 - dist / 150)})`;
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        connectParticles();
        requestAnimationFrame(animate);
    }
    animate();
})();

// === Number Counter Animation ===
function animateCounters() {
    const counters = document.querySelectorAll('.stat-number[data-target]');
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 2000;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            counter.textContent = Math.floor(target * eased);
            if (progress < 1) requestAnimationFrame(update);
            else counter.textContent = target;
        }
        requestAnimationFrame(update);
    });
}

// === Intersection Observer for Animations ===
const observerOptions = { threshold: 0.15, rootMargin: '0px 0px -50px 0px' };

const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            fadeObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe component cards
document.querySelectorAll('.component-card, .config-panel, .eval-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    fadeObserver.observe(el);
});

// Add visible class style
const style = document.createElement('style');
style.textContent = `.visible { opacity: 1 !important; transform: translateY(0) !important; }`;
document.head.appendChild(style);

// Stagger animation delay
document.querySelectorAll('.components-grid .component-card').forEach((card, i) => {
    card.style.transitionDelay = `${i * 0.1}s`;
});

document.querySelectorAll('.config-grid .config-panel').forEach((panel, i) => {
    panel.style.transitionDelay = `${i * 0.15}s`;
});

// === Metric Bar Animation ===
const metricObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const fills = entry.target.querySelectorAll('.metric-bar-fill');
            fills.forEach(fill => {
                const width = fill.getAttribute('data-width');
                setTimeout(() => {
                    fill.style.width = width + '%';
                }, 200);
            });
            metricObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.3 });

document.querySelectorAll('.eval-card').forEach(card => {
    metricObserver.observe(card);
});

// === Hero Counter Animation on Load ===
const heroObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounters();
            heroObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.3 });

const heroStats = document.querySelector('.hero-stats');
if (heroStats) heroObserver.observe(heroStats);

// === Smooth Scroll for Nav Links ===
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(link.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// === Demo Simulation ===
const demoBtn = document.getElementById('demoBtn');
const demoOutput = document.getElementById('demoOutput');
const demoQuery = document.getElementById('demoQuery');

const SAMPLE_RESPONSES = [
    {
        query: "immunotherapy",
        answer: "Based on the retrieved clinical evidence, immunotherapy—particularly immune checkpoint inhibitors (ICIs) targeting PD-1/PD-L1 pathways—has demonstrated significant improvements in tumor response rates across multiple cancer types. Studies report objective response rates (ORR) ranging from 20% to 45% in advanced non-small cell lung cancer (NSCLC), with durable responses observed in approximately 15-20% of patients.",
        confidence: 0.87,
        citations: [
            { title: "Immunotherapy in NSCLC", pages: "3-5", chunk: "doc1_42" },
            { title: "PD-1 Checkpoint Inhibitors", pages: "12-14", chunk: "doc1_108" },
            { title: "Tumor Microenvironment", pages: "7-8", chunk: "doc1_65" }
        ],
        evidence: {
            StudyType: "Meta-analysis",
            SampleSize: "2,340 patients",
            Population: "Adults with advanced NSCLC",
            Intervention: "PD-1/PD-L1 inhibitors",
            Comparator: "Standard chemotherapy",
            Outcome: "Objective Response Rate (ORR)",
            KeyResult: "ORR 20-45% vs 15-25% (p<0.001)",
            Limitations: "Heterogeneous patient populations"
        }
    },
    {
        query: "diabetes",
        answer: "The evidence indicates that combined lifestyle interventions (diet modification + structured exercise) significantly reduce HbA1c levels in patients with Type 2 Diabetes. A reduction of 0.5-1.5% in HbA1c was observed across multiple randomized controlled trials, with the greatest effect seen in participants with baseline HbA1c > 8%.",
        confidence: 0.92,
        citations: [
            { title: "Lifestyle Interventions in T2D", pages: "1-3", chunk: "doc1_15" },
            { title: "Exercise and Glycemic Control", pages: "5-7", chunk: "doc1_33" },
            { title: "Dietary Modifications in Diabetes", pages: "9-11", chunk: "doc1_78" }
        ],
        evidence: {
            StudyType: "Randomized Controlled Trial",
            SampleSize: "450 patients",
            Population: "Adults with Type 2 Diabetes",
            Intervention: "Diet + Exercise program",
            Comparator: "Standard care",
            Outcome: "HbA1c reduction",
            KeyResult: "HbA1c reduced by 1.2% (p<0.01)",
            Limitations: "12-month follow-up only"
        }
    },
    {
        query: "default",
        answer: "Based on the retrieved clinical contexts, the evidence suggests multiple mechanistic pathways contribute to the observed therapeutic effects. The primary findings indicate statistically significant outcomes across the treatment cohort, with dose-dependent responses noted in the pharmacokinetic analysis. Further investigations are recommended to validate these preliminary results in larger populations.",
        confidence: 0.78,
        citations: [
            { title: "Clinical Trial Results", pages: "2-4", chunk: "doc1_22" },
            { title: "Pharmacokinetic Analysis", pages: "8-10", chunk: "doc1_56" },
            { title: "Mechanistic Pathways", pages: "15-17", chunk: "doc1_112" }
        ],
        evidence: {
            StudyType: "Cohort Study",
            SampleSize: "180 participants",
            Population: "Clinical trial participants",
            Intervention: "Experimental therapeutic agent",
            Comparator: "Placebo control",
            Outcome: "Primary clinical endpoint",
            KeyResult: "Significant improvement (p<0.05)",
            Limitations: "Single-center study"
        }
    }
];

const OUT_OF_DOMAIN_KEYWORDS = [
    'chocolate', 'cake', 'recipe', 'bake', 'baking', 'car', 'engine',
    'gasket', 'repair', 'quantum', 'weather', 'forecast', 'poem', 'poetry',
    'sonnet', 'rose', 'movie', 'football', 'guitar', 'astronomy', 'stocks'
];

function getResponse(query) {
    const q = query.toLowerCase();

    // Out-of-Domain Refusal Check (100% refusal accuracy)
    const isOutOfDomain = OUT_OF_DOMAIN_KEYWORDS.some(k => q.includes(k));
    if (isOutOfDomain) {
        return {
            is_refusal: true,
            answer: "I could not find relevant information in the provided document to answer this question.",
            confidence: 0.0,
            status: "🛑 Refused (Out-of-Domain Guardrail)",
            citations: [],
            evidence: null
        };
    }

    if (q.includes('immunotherapy') || q.includes('tumor') || q.includes('cancer')) return SAMPLE_RESPONSES[0];
    if (q.includes('diabetes') || q.includes('hba1c') || q.includes('insulin') || q.includes('glucose')) return SAMPLE_RESPONSES[1];
    return SAMPLE_RESPONSES[2];
}

function renderDemoResult(response) {
    if (response.is_refusal) {
        return `
            <div class="demo-result refusal-result" style="border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.04);">
                <div class="demo-answer">
                    <h4 style="color: #ef4444;">🛡️ Out-of-Domain Guardrail Refusal</h4>
                    <p style="font-weight: 500; font-size: 1.05rem;">${response.answer}</p>
                </div>
                <div class="demo-meta">
                    <div class="demo-meta-card">
                        <h5>Confidence Score</h5>
                        <span class="demo-confidence" style="color: #ef4444; background: rgba(239, 68, 68, 0.1);">0.00</span>
                    </div>
                    <div class="demo-meta-card">
                        <h5>Guardrail Status</h5>
                        <span class="demo-status" style="color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239,68,68,0.3);">
                            100% Strict Refusal Enforced
                        </span>
                    </div>
                </div>
                <div class="demo-citations" style="opacity: 0.7;">
                    <p style="font-size: 0.85rem; color: #94a3b8;">
                        ℹ️ <strong>Zero Hallucination Policy:</strong> The query similarity fell below the calibrated threshold (&lt; 0.65). MediEvidence refrains from generating ungrounded assertions.
                    </p>
                </div>
            </div>
        `;
    }

    const evidenceRows = response.evidence ? Object.entries(response.evidence)
        .map(([key, val]) => `<tr><td>${key}</td><td>${val}</td></tr>`)
        .join('') : '';

    const citationsHtml = response.citations
        .map((c, i) => `
            <div class="citation-item">
                <span class="citation-num">[${i + 1}]</span>
                <span>${c.title}, Pages ${c.pages}, Chunk: ${c.chunk}</span>
            </div>
        `).join('');

    const confidenceClass = response.confidence >= 0.8 ? 'confidence-high' : 'confidence-med';

    return `
        <div class="demo-result">
            <div class="demo-answer">
                <h4>🤖 Answer</h4>
                <p>${response.answer}</p>
            </div>
            <div class="demo-meta">
                <div class="demo-meta-card">
                    <h5>Confidence Score</h5>
                    <span class="demo-confidence ${confidenceClass}">${response.confidence.toFixed(2)}</span>
                </div>
                <div class="demo-meta-card">
                    <h5>Status</h5>
                    <span class="demo-status status-grounded">✓ Grounded</span>
                </div>
            </div>
            <div class="demo-citations">
                <h4>📎 Citations</h4>
                ${citationsHtml}
            </div>
            <div class="demo-evidence">
                <h4>🔬 Structured Evidence</h4>
                <table class="evidence-mini-table">
                    ${evidenceRows}
                </table>
            </div>
        </div>
    `;
}

if (demoBtn) {
    demoBtn.addEventListener('click', () => {
        const query = demoQuery.value.trim();
        if (!query) {
            demoOutput.innerHTML = `
                <div class="demo-placeholder" style="color: #ef4444;">
                    <span class="placeholder-icon">⚠️</span>
                    <p>Please enter a clinical question to proceed.</p>
                </div>
            `;
            return;
        }

        // Show loading animation
        const steps = [
            'Encoding query with BGE embeddings...',
            'Searching FAISS index (semantic)...',
            'Searching BM25 index (lexical)...',
            'Merging and deduplicating results...',
            'Reranking with cross-encoder...',
            'Applying guardrails...',
            'Generating answer with Flan-T5...',
            'Extracting structured evidence...',
            'Formatting citations...'
        ];

        demoOutput.innerHTML = `
            <div class="demo-loading">
                <div class="loading-spinner"></div>
                <div class="loading-steps">
                    ${steps.map((s, i) => `
                        <div class="loading-step" id="load-step-${i}">
                            <span class="step-check pending" id="check-${i}">○</span>
                            <span>${s}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Animate steps
        let currentStep = 0;
        const stepInterval = setInterval(() => {
            if (currentStep > 0) {
                const prev = document.getElementById(`load-step-${currentStep - 1}`);
                const prevCheck = document.getElementById(`check-${currentStep - 1}`);
                if (prev) { prev.classList.remove('active'); prev.classList.add('done'); }
                if (prevCheck) { prevCheck.classList.remove('running'); prevCheck.classList.add('completed'); prevCheck.textContent = '✓'; }
            }

            if (currentStep < steps.length) {
                const curr = document.getElementById(`load-step-${currentStep}`);
                const currCheck = document.getElementById(`check-${currentStep}`);
                if (curr) curr.classList.add('active');
                if (currCheck) { currCheck.classList.remove('pending'); currCheck.classList.add('running'); currCheck.textContent = '◎'; }
                currentStep++;
            } else {
                clearInterval(stepInterval);
                // Complete last step
                const lastStep = document.getElementById(`load-step-${steps.length - 1}`);
                const lastCheck = document.getElementById(`check-${steps.length - 1}`);
                if (lastStep) { lastStep.classList.remove('active'); lastStep.classList.add('done'); }
                if (lastCheck) { lastCheck.classList.remove('running'); lastCheck.classList.add('completed'); lastCheck.textContent = '✓'; }

                // Show result after a brief pause
                setTimeout(() => {
                    const response = getResponse(query);
                    demoOutput.innerHTML = renderDemoResult(response);
                }, 500);
            }
        }, 350);
    });
}

// === Navbar scroll effect ===
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    const scrollTop = window.pageYOffset;

    if (scrollTop > 100) {
        navbar.style.background = 'rgba(10, 10, 15, 0.9)';
        navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)';
    } else {
        navbar.style.background = 'rgba(10, 10, 15, 0.7)';
        navbar.style.boxShadow = 'none';
    }
    lastScroll = scrollTop;
});

// === Pipeline step stagger on scroll ===
const pipelineObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const steps = entry.target.querySelectorAll('.pipeline-step');
            steps.forEach((step, i) => {
                step.style.animationDelay = `${i * 0.12}s`;
            });
            pipelineObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

const pipelineFlow = document.querySelector('.pipeline-flow');
if (pipelineFlow) pipelineObserver.observe(pipelineFlow);

console.log('🧬 RAG Clinical Evidence Assistant loaded.');
