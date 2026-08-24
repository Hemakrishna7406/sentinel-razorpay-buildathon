# Sentinel — Demo Script

**Audience**: Razorpay engineering panel.
**Duration**: 5 minutes.
**Goal**: Prove the architecture works, the ML is real, and the fail-closed guarantee is ironclad.

---

### Beat 1: The Pitch Page (0:00 - 1:00)

**Action**: Open `http://127.0.0.1:8000/`

**Speaker**:
"Sentinel is a behavioral risk engine for autonomous AI financial agents.

The core problem we're solving is that static authorization isn't enough for AI. Authorization tells us what an agent is *allowed* to do. Sentinel tells us when that agent stops behaving like the agent we *trusted*.

*(Scroll to 01 - Agent)*
Before Sentinel makes any decision, it builds a statistical baseline of an agent's normal behavior.

*(Scroll to 02 - Intent)*
When an intent comes in, it passes through our pipeline.

*(Scroll to 03 - Drift)*
We measure the drift. If an agent is compromised—say, via prompt injection—its transaction velocity spikes, amounts deviate, and it sends money to novel recipients. The Trust Pulse you see here visualizes that drift.

*Dashboard zooms in on the ML tab*

This isn't a rules engine. It's an XGBoost model evaluated on a temporally-split held-out test set. We achieved 97.7% precision with a 10.0% false escalation rate.

*Crucially*, that 10% isn't an ML failure—it is the intentional friction applied by the policy layer when completely unseen agents start making transactions. We proactively escalate them until a baseline is formed, ensuring fail-safe operation during cold starts.

*(Scroll to 05 - Containment)*
But detection without enforcement is useless. Sentinel issues a cryptographically signed Capability Token. No token, no execution. Fail closed, always."

---

### Beat 2: Live Dashboard & Agent Overview (1:00 - 2:00)

**Action**: Click "Open Dashboard →" (Navigates to `http://127.0.0.1:8000/dashboard`)

**Speaker**:
"Let's look at the operational dashboard. Here we see the active agents.

Notice `agent_0x91`. Its drift score is high. It's normally doing 4 transactions an hour, but it's suddenly doing 14. Sentinel has automatically flagged it as Suspicious."

---

### Beat 3: Policy Compilation (2:00 - 3:00)

**Action**: Click "Policy Rules" tab in sidebar.

**Speaker**:
"Before the ML model even sees an intent, we run it through our deterministic Natural Language Policy Compiler.

Let's say we want a hard stop on any massive refund."

**Action**: Type in the box: `ESCALATE IF action_type = refund AND amount > 50000000` and click "Add Rule".

**Speaker**:
"This compiles instantly into an executable predicate. If an intent hits this rule, it escalates immediately. If a field is missing in the context, it fails closed and escalates anyway."

---

### Beat 4: Live Evaluation & SHAP Explanations (3:00 - 4:00)

**Action**: Click "Evaluate" tab.

**Speaker**:
"Let's submit a live intent for `agent_0x91`. We'll ask it to do a payout of ₹92,000 to an unknown external bank."

**Action**: Fill the Evaluate form. Set Action to `payout`, Amount to `9200000`, Recipient to `bank_unknown_ext_9`. Click "Evaluate Intent".

**Speaker**:
"It escalated. Why? Sentinel gives us real-time SHAP feature contributions.

*(Point to the feature bars)*
The amount deviation and the recipient novelty were the primary drivers pushing the risk score up, overriding the agent's previously safe history."

---

### Beat 5: Simulation & Proof of Holdout (4:00 - 5:00)

**Action**: Click "Simulate" tab. Click "Run Simulation".

**Speaker**:
"Finally, we can run batch simulations across thousands of synthetic intents.

Our synthetic data generator creates abuse bursts, slow abuse, and seasonal spikes. The model correctly learns that a seasonal spike in volume is safe, but an abuse burst to novel recipients is high risk.

And because this is a real engineering project, the entire dataset generation, training pipeline, ablation studies, and evaluation metrics are fully reproducible with three commands in the terminal."

*(End Demo)*
