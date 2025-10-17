# ADR-003: Local Training Hardware Evaluation & Cloud Backup Options

**Status**: APPROVED ✅  
**Date**: 2026-01-09  
**Decision Maker**: MLOps Architect  
**Context**: Feasibility assessment of local training on a MacBook M1 Air with 16GB RAM.

---

## 📊 Hardware Capability Assessment

### Hardware Specifications

```
Device:     MacBook Air M1 (2020/2021)
CPU:        Apple M1 (8-core: 4P + 4E)
GPU:        Apple M1 (7/8-core integrated)
RAM:        16GB Unified Memory
Storage:    SSD (Assumed 256GB+)
TDP:        ~15W (Fanless passive cooling)
```

---

## ✅ Local Training Feasibility Analysis

### Scenario 1: Ollama Llama 3.2 3B (Sentiment Analysis)

**Model Specifications**:

- Parameters: **3B** (3 Billion parameters)
- Quantization: **Q4_0** (4-bit quantization)
- RAM Requirements: ~**2GB RAM**
- Inference Speed: ~**20-30 tokens/sec** (M1 Optimized)

**Result**: ✅ **Fully Feasible**

```
Reasoning:
1. Ollama is optimized for Apple Silicon (Metal API).
2. 3B model memory footprint is < 3GB, well below the 16GB limit.
3. Only inference is required; no fine-tuning is needed.
4. Daily throughput: 50 Reddit posts × 200 words ≈ 10,000 tokens.
5. Estimated time: 10,000 tokens ÷ 25 tokens/sec ≈ 6.6 minutes.

Cost: $0 (Local execution)
```

**Practical Testing Command**:

```bash
# Install Ollama
brew install ollama

# Pull model
ollama pull llama3.2:3b

# Benchmark inference speed
time ollama run llama3.2:3b "Classify sentiment: Bitcoin hits new high!"
```

---

### Scenario 2: Traditional ML Model Training (RandomForest, XGBoost, LogisticRegression)

**Data Scale Estimation**:

```
Training Data Volume:
- 60 days of historical data (Initial stage)
- 1 entry per day (Daily OHLC + Sentiment Score)
- Feature Count: ~30 features (Technical indicators + Sentiment features)
- Data Size: 60 rows × 30 columns ≈ 0.1MB (Extremely small)

Model Complexity:
- RandomForest: 100 trees, depth=10
- XGBoost: 100 boosting rounds
- LogisticRegression: L2 regularization
```

**Result**: ✅ **Fully Feasible**

```
Reasoning:
1. Data volume is minimal (< 1MB), no GPU acceleration required.
2. Scikit-learn/XGBoost are highly efficient on CPU.
3. Estimated training time: < 5 seconds per model.
4. Memory usage: < 500MB.
5. M1 CPU performance exceeds many Intel Xeon server instances.

Cost: $0 (Local execution)
```

**Resource Monitoring**:

```bash
# Monitor resource usage during training
python -m memory_profiler train_model.py

# Expected Results:
# Peak memory: ~800MB
# CPU usage: 60-80%
# Time: < 10 seconds
```

---

### Scenario 3: Future Scaling Scenarios (Requires Re-evaluation)

| Scenario                  | Data Volume         | M1 16GB Feasibility | Recommended Plan          |
| ------------------------- | ------------------- | ------------------- | ------------------------- |
| **Longer History**        | 1 Year (365 Days)   | ✅ Feasible         | Local training is fine    |
| **Increased Features**    | 100+ Features       | ✅ Feasible         | Local training is fine    |
| **Deep Learning (LSTM)**  | 1 Year + Sequences  | ⚠️ Feasible but slow| Recommend Cloud (GPU)     |
| **Fine-tune Llama 3.2**   | LoRA Fine-tuning    | ❌ Not Feasible     | Cloud GPU Mandatory       |
| **Large-scale Backtest**  | 10 Years            | ✅ Feasible         | Local, batch processing   |
| **Real-time Inference**   | API Service         | ✅ Feasible         | FastAPI + M1 is enough    |

---

## 🎯 **Conclusion: Your M1 Air 16GB is More Than Sufficient!**

### Why You Don't Need to Worry:

1. **Lightweight Model Selection by Design**:

   - Llama 3.2 **3B** (not 70B or 405B).
   - Traditional ML instead of Deep Learning (Transformers).
   - Daily level data instead of high-frequency tick data.

2. **M1 Chip Advantages**:

   - Unified Memory Architecture (CPU/GPU share 16GB).
   - Metal API Acceleration (Native support in Ollama).
   - High performance-per-watt (fan might not even spin during training).

3. **Cost Comparison**:
   ```
   Local M1 Training:    $0/month (Already owned hardware)
   Cheapest Cloud Plan:  Starting at $8.71/month (Rental required)
   ```

---

## 💰 Cloud Backup Options (If needed in the future)

### Option A: Hetzner Cloud (Planned in PLAN.md)

**Scenario**: Production deployment, not for training.

```
Model: CPX21 (2 vCPU, 4GB RAM)
Price: €8.71/month ≈ $9.50/month
Purpose: K3s deployment (Inference service)
Unsuitable for: Deep Learning training (No GPU)
```

---

### Option B: Hetzner Cloud GPU (Deep Learning Training Only)

**Scenario**: Fine-tune Llama or train LSTM models.

```
Model: CCX23 GPU (8 vCPU, 32GB RAM, NVIDIA A10)
Price: ~€1.20/hour ≈ $1.30/hour
Strategy: Start on demand, shut down after training.
Estimated Cost:
  - Weekly training (1x 2hrs) = $2.60/week
  - Monthly cost: ~$10.40/month (vs AWS p3.2xlarge at $3.06/hr)

Advantages:
✅ 58% cheaper than AWS GPU.
✅ EU Data Privacy protection.
✅ Simple Terraform integration.
```

**Terraform Example**:

```hcl
# infra/hetzner/gpu-training.tf
resource "hcloud_server" "gpu_trainer" {
  count       = var.enable_gpu_training ? 1 : 0
  name        = "alphapulse-gpu-trainer"
  server_type = "ccx23"  # GPU instance
  image       = "ubuntu-22.04"

  labels = {
    purpose = "ml-training"
    auto_shutdown = "true"  # Automatically shut down after training
  }
}
```

---

### Option C: Vast.ai / RunPod (Cheapest GPU Rental)

**Scenario**: Occasional need for powerful GPU training.

```
Platform: Vast.ai (P2P GPU marketplace)
Model: RTX 3090 (24GB VRAM)
Price: ~$0.20-0.40/hour (Community pricing)
Strategy: Rent only when needed, billed by the second.

Estimated Monthly Cost:
  - Monthly training (4x 2hrs @ $0.30) = $2.40/month

Advantages:
✅ Extremely low price (90% cheaper than AWS).
✅ Wide variety of GPUs.
✅ Docker friendly.

Disadvantages:
❌ Lower reliability (personal hosts).
❌ Additional platform learning curve.
❌ Potential slow data transfer speeds.
```

**Workflow**:

```bash
# 1. Register Vast.ai account
# 2. Search for suitable GPUs
vastai search offers 'gpu_name=RTX 3090 reliability>0.95'

# 3. Rent instance
vastai create instance <offer_id> --image pytorch/pytorch:latest

# 4. Upload script and execute
vastai scp train_model.py <instance_id>:/workspace/

# 5. Destroy instance immediately after training
vastai destroy instance <instance_id>
```

---

### Option D: AWS EC2 Spot Instances (Elastic Training)

**Scenario**: Need for AWS ecosystem integration.

```
Model: g4dn.xlarge (4 vCPU, 16GB RAM, T4 GPU)
Price:
  - On-Demand: $0.526/hour
  - Spot Instance: ~$0.158/hour (70% discount)

Strategy:
  - Use Spot Instances.
  - Enable interruption notifications (120-second warning).
  - Implement automated checkpointing.

Estimated Monthly Cost:
  - Weekly training (1x 3hrs @ $0.158) = $1.90/month

Advantages:
✅ Seamless integration with S3 (already in use).
✅ Simple Terraform management.
✅ Can be automated for start/stop.

Disadvantages:
❌ Risk of interruption (requires checkpoints).
❌ Still more expensive than Hetzner.
```

**Terraform Automation Example**:

```hcl
# infra/aws/spot-training.tf
resource "aws_spot_instance_request" "ml_trainer" {
  count         = var.enable_spot_training ? 1 : 0
  ami           = data.aws_ami.ubuntu_gpu.id
  instance_type = "g4dn.xlarge"
  spot_price    = "0.20"  # Maximum willing price

  user_data = templatefile("${path.module}/scripts/setup-training.sh", {
    s3_bucket = aws_s3_bucket.mlflow_artifacts.id
  })

  tags = {
    Name = "alphapulse-spot-trainer"
    AutoShutdown = "true"
  }
}

# Automation script: Shutdown after training
# scripts/train-and-shutdown.sh
#!/bin/bash
python train_model.py
aws s3 sync /workspace/models/ s3://alphapulse-models/
sudo shutdown -h now  # Auto-shutdown to save costs
```

---

## 🎯 My Recommendations (Cost-Optimal Strategy)

### **Phase 1: MVP Development (Now - Week 3)**

```
Hardware: MacBook M1 Air 16GB (Local)
Cost: $0
Reason: Fully capable of handling current data volume and model complexity.
```

### **Phase 2: Production Deployment (Week 4+)**

```
Service: Hetzner CPX21 (Inference Service)
Cost: $9.50/month
Purpose: API Service + K3s Cluster
```

### **Phase 3: Model Optimization (Optional)**

```
Service: Vast.ai RTX 3090 (On-demand Training)
Cost: ~$2.40/month (4x sessions/month)
Purpose: Deep Learning experiments, Hyperparameter tuning.
```

### **Total Cost Comparison**

```
Local Development (Week 1-3):    $0.00
Production Deployment (Week 4+): $9.50/month
Occasional GPU Training (Opt):    $2.40/month
─────────────────────────────────
Total:                           ~$11.90/month

vs. Traditional Solutions:
❌ AWS EKS + EC2 + GPU:         $150+/month
✅ Savings:                      92% Cost Reduction
```

---

## 🚀 Immediate Action Plan

### Step 1: Test Local Training Capability (Complete Today)

```bash
# 1. Install Ollama and test
brew install ollama
ollama pull llama3.2:3b
time ollama run llama3.2:3b "Test sentiment analysis"

# 2. Monitor resource usage
# Terminal 1: Start monitor
top -pid $(pgrep ollama)

# Terminal 2: Run test script
cd mage_pipeline/pipelines/reddit_sentiment_pipeline
python test_ollama_performance.py

# Expected Results:
# ✅ Memory usage: < 3GB
# ✅ CPU usage: 60-80%
# ✅ Inference speed: 20+ tokens/sec
# ✅ Temperature: < 70°C (M1 cooling is excellent)
```

### Step 2: Benchmark (Complete this week)

Establish performance baseline:

```python
# scripts/benchmark_local_training.py
import time
import psutil
from train_model import train_all_models

def benchmark():
    start_time = time.time()
    start_memory = psutil.virtual_memory().used

    # Train all models
    train_all_models()

    end_time = time.time()
    end_memory = psutil.virtual_memory().used

    print(f"Training time: {end_time - start_time:.2f}s")
    print(f"Memory used: {(end_memory - start_memory) / 1024**3:.2f}GB")

# Expected Results (M1 16GB):
# Training time: < 30s
# Memory used: < 2GB
# Conclusion: Cloud is currently unnecessary.
```

---

## 📚 Resources

- [Ollama Apple Silicon Performance](https://github.com/ollama/ollama/blob/main/docs/metal.md)
- [Hetzner Cloud GPU Pricing](https://www.hetzner.com/cloud/gpu)
- [Vast.ai GPU Marketplace](https://vast.ai/)
- [AWS Spot Instance Best Practices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html)

---

## ✅ Decision

**APPROVED**: Use MacBook M1 Air 16GB for local training.

**Reasons**:

1. Current data volume and model complexity are perfectly suited for local training.
2. Zero-cost advantage aligns with project FinOps principles.
3. M1 performance exceeds most cloud CPU instances.
4. Easily scalable to cloud GPU whenever necessary (starting from $2.40/month).

**Next Step**: Execute Step 1 Local Performance Test to prove feasibility.

---

**Last Updated**: 2026-01-09  
**Owner**: MLOps Architect  
**Status**: Ready for Implementation ✅