# NurosOS — Keywords & Repository Description

> Canonical keyword clusters and repository description, optimized for search engines (SEO), answer engines (AEO), and generative engines (GEO). Available in English and فارسی.

---

## Repository Description (GitHub "About" field)

> **EN (350 chars max):** NurosOS is a bio-inspired neuromorphic operating system (Rust + Python) that runs the complete *Drosophila* connectome (125M synapses) as an event-driven spiking network. Targets x86, ARM, Intel Loihi 2, FPGA. Apache-2.0.

> **FA (فارسی):** NurosOS یک سیستم‌عامل عصب‌شکل‌نگرانه (Neuromorphic OS) متن‌باز است که با زبان Rust و Python نوشته شده و کانکتوم کامل مگس میوه *Drosophila* (۱۲۵ میلیون سیناپس) را به‌صورت یک شبکه‌ی اسپایکی(event-driven) اجرا می‌کند. هدف: راندمان انرژی ۱۰۰۰ برابری نسبت به GPU.

---

## Short Taglines (≤80 chars)

1. `Bio-inspired neuromorphic OS — runs the Drosophila connectome as software.`
2. `Rust microkernel + Python DSL for spiking neural networks on Loihi & FPGA.`
3. `Event-driven OS with 5% sparse spiking — 1000× lower energy than GPUs.`
4. `The first OS that treats memory as synaptic weights, not files.`
5. `Digital Biology: cognition as an executable system process.`

---

## Keyword Clusters

### Cluster 1 — Core Identity

```
neuromorphic operating system
bio-inspired operating system
spiking neural network OS
event-driven operating system
cognitive operating system
digital biology
biological computing substrate
```

### Cluster 2 — Biological Foundation

```
Drosophila melanogaster connectome
fruit fly connectome
FlyWire connectome
whole-brain connectome
synapse-resolution connectome
125 million synapses
140000 neurons
neuropil
mushroom body
antennal lobe
central complex
lateral horn
Kenyon cells
projection neurons
mbon (mushroom body output neurons)
local interneurons
```

### Cluster 3 — Algorithms & Models

```
Leaky Integrate-and-Fire (LIF)
Hodgkin-Huxley
Izhikevich model
Spike-Timing-Dependent Plasticity (STDP)
Hebbian learning
dopamine-modulated plasticity
short-term facilitation
short-term depression
lateral inhibition
sparse coding
winner-take-all
Hassenstein-Reichardt detector
elementary motion detector (EMD)
attractor network
Hopfield network
```

### Cluster 4 — Architecture & Systems

```
microkernel
no_std Rust kernel
zero-copy IPC
SPSC ring buffer
lock-free data structures
event-driven scheduler
Sparse Propagation Protocol (SPP)
sparsity threshold 5%
associative memory store
content-addressed memory
Hopfield attractor memory
fault tolerance
neuroplasticity emulation
compensatory sprouting
dynamic remapping
```

### Cluster 5 — Hardware Targets

```
neuromorphic silicon
Intel Loihi 2
Intel Loihi 1
IBM TrueNorth
SpiNNaker
BrainScaleS
FPGA neuromorphic
custom neuromorphic hardware
x86_64 emulation
ARM Cortex-M
ARM Neoverse
RISC-V neuromorphic
picojoule per spike
```

### Cluster 6 — Languages & Tooling

```
Rust 1.75
Python 3.10
domain-specific language (DSL)
SynapseLang
NIR (Neuromorphic Intermediate Representation)
msgpack bytecode
HDF5 connectome format
FlyWire .h5 dataset
cargo workspace
pyproject.toml
ruff
clippy
criterion benchmarks
```

### Cluster 7 — Energy & Efficiency

```
Von Neumann bottleneck
memory-compute collocation
energy-efficient computing
picojoule computing
low-power AI
edge AI
edge inference
1000× power reduction
sparse activation
biological energy budget
mitochondrial ATP supply
data movement reduction
on-chip learning
```

### Cluster 8 — Applications

```
pattern recognition
associative memory
olfactory classification
object tracking
motion detection
locomotion pattern generation
courtship song generation
phototaxis
obstacle avoidance
neurological disorder simulation
epilepsy simulation
memory degradation
pharmaceutical testing
digital twin
brain simulation
```

### Cluster 9 — Scientific Context

```
connectomics
neuroscience
computational neuroscience
systems neuroscience
neuromorphic engineering
bio-inspired computing
brain-inspired computing
spiking neural networks (SNN)
spike-based computing
event-based vision
event-based sensing
```

### Cluster 10 — License & Community

```
open-source
Apache License 2.0
permissive license
commercial-friendly
research software
alpha release
academic software
community-driven
contributions welcome
GitFlow workflow
peer review
CI/CD
```

---

## Long-Form Description (for indexing)

### English

NurosOS is an open-source, Apache-2.0 licensed, bio-inspired neuromorphic operating system implemented in Rust and Python. It runs the complete *Drosophila melanogaster* connectome — 140,000 neurons and 125 million synaptic connections, derived from the 2026 FlyWire release — as an event-driven spiking neural network. The project reverses the traditional Von Neumann bottleneck by collocating memory and compute at the synapse level, and by enforcing a 5% sparsity cap per scheduler tick (the Sparse Propagation Protocol, or SPP) that matches the observed activation rate in the *Drosophila* central brain.

The system is organized as a three-layer stack: (1) a Rust `no_std` microkernel with an event-driven scheduler, zero-copy SPSC ring buffers for synaptic channels, and an Associative Memory Store that replaces the filesystem with content-addressed retrieval; (2) SynapseLang, a Python domain-specific language that compiles high-level cognitive function descriptions into hardware-agnostic NIR bytecode; and (3) a Rust Hardware Abstraction Layer with trait-based drivers for x86_64 emulation, ARM Cortex-M, Intel Loihi 2, IBM TrueNorth, and custom FPGA arrays. The HAL implements dynamic remapping — a neuroplasticity emulation that reroutes through alternative pathways when a physical core fails, mimicking biological compensatory sprouting after brain injury.

Core algorithms include Leaky Integrate-and-Fire (LIF) neurons with *Drosophila* mushroom-body Kenyon cell parameters, Spike-Timing-Dependent Plasticity (STDP) with symmetric LTP/LTD windows, Hebbian learning, dopamine-modulated plasticity, lateral inhibition, and axonal delay-line modeling. Target applications include associative memory, olfactory classification, object tracking, locomotion pattern generation, and pharmaceutical digital-twin simulations of neurological disorders such as epilepsy and memory degradation.

Projected performance on Intel Loihi 2 (v0.3.0 release candidate): 0.014 mJ per inference and 6 µs p50 latency for a 1024-dimensional olfactory classification task — a 1286× energy reduction compared to PyTorch on an A100 GPU.

### فارسی (Persian)

NurosOS یک سیستم‌عامل عصب‌شکل‌نگرانه (Neuromorphic Operating System) متن‌باز با مجوز Apache-2.0 است که با زبان‌های Rust و Python پیاده‌سازی شده است. این سیستم کانکتوم کامل مگس میوه *Drosophila melanogaster* — شامل ۱۴۰ هزار نورون و ۱۲۵ میلیون اتصال سیناپسی، برگرفته از انتشار FlyWire در سال ۲۰۲۶ — را به‌صورت یک شبکه‌ی عصبی اسپایکی(event-driven) اجرا می‌کند.

پروژه با جای‌گذاری حافظه و محاسبه در سطح سیناپس و اعمال محدودیت ۵ درصدی فعال‌بودن نورون‌ها در هر تیک زمان‌بند (الگوریتم Sparse Propagation Protocol یا SPP) — که با نرخ فعال‌سازی مشاهده‌شده در مغز مرکزی مگس میوه مطابقت دارد — گلوگاه سنتی ون‌نویمان را برطرف می‌کند.

معماری سه‌لایه‌ی NurosOS شامل است: (۱) میکروکرنل Rust با زمان‌بند رویدادمحور، بافرهای حلقوی بدون کپی برای کانال‌های سیناپسی، و Associative Memory Store که جایگزین سیستم فایل سنتی با بازیابی محتوا-محور می‌شود؛ (۲) SynapseLang، یک زبان دامنه-ویژه‌ی Python که توابع شناختی سطح بالا را به بایت‌کد سخت‌افزار-آگنوستیک NIR کامپایل می‌کند؛ و (۳) لایه‌ی انتزاع سخت‌افزار (HAL) با درایورهای مبتنی بر trait برای x86_64، ARM Cortex-M، Intel Loihi 2، IBM TrueNorth و آرایه‌های FPGA.

الگوریتم‌های اصلی شامل نورون‌های Leaky Integrate-and-Fire با پارامترهای سلول‌های Kenyon در بدنه‌ی قارچی مگس، پلاستیسیته‌ی وابسته به زمان‌بندی اسپایک (STDP)، یادگیری هبی، پلاستیسیته‌ی تعدیل‌شونده با دوپامین، بازداری جانبی و مدل‌سازی تأخیر آکسونی است. کاربردهای هدف شامل حافظه‌ی تداعی‌گرا، دسته‌بندی بویایی، ردیابی شیء، تولید الگوی حرکتی و شبیه‌سازی‌های دارویی (Digital Twin) از اختلالات عصبی مانند صرع و تحلیل حافظه است.

عملکرد پیش‌بینی‌شده روی Intel Loihi 2 (نسخه‌ی v0.3.0): ۰٫۰۱۴ میلی‌ژول به ازای هر استنتاج و تأخیر ۶ میکروثانیه برای دسته‌بندی بویایی ۱۰۲۴-بُعدی — کاهش ۱۲۸۶ برابری مصرف انرژی نسبت به PyTorch روی GPU مدل A100.

---

## Hashtags (for social sharing)

```
#NurosOS #NeuromorphicComputing #SpikingNeuralNetworks #Drosophila #Connectome
#BioInspired #OperatingSystem #RustLang #Python #IntelLoihi #LowPowerAI
#EdgeAI #SNN #STDP #LIF #SynapseLang #DigitalBiology #OpenSource
#VonNeumannBottleneck #PicojouleComputing #Neuroscience #BrainInspired
#NeuromorphicOS #CognitiveComputing #FaultTolerance #AssociativeMemory
```

---

## SEO Meta Tags (for HTML documentation site)

```html
<title>NurosOS — Bio-Inspired Neuromorphic Operating System (Drosophila Connectome)</title>
<meta name="description" content="Open-source Rust + Python neuromorphic operating system that runs the complete Drosophila connectome (125M synapses) as an event-driven spiking network. 1000× lower energy than GPUs on Intel Loihi 2.">
<meta name="keywords" content="neuromorphic operating system, spiking neural networks, Drosophila connectome, bio-inspired computing, Intel Loihi, Rust kernel, SynapseLang, Sparse Propagation Protocol, associative memory, STDP, LIF neuron, Von Neumann bottleneck, picojoule computing, edge AI">
<meta name="author" content="NurosOS Contributors">
<meta name="robots" content="index, follow">
<meta property="og:title" content="NurosOS — Bio-Inspired Neuromorphic Operating System">
<meta property="og:description" content="Runs the complete Drosophila connectome (125M synapses) as an event-driven spiking network. 1000× lower energy than GPUs on Intel Loihi 2.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://github.com/modarresi1913/NurosOS">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="NurosOS — Bio-Inspired Neuromorphic OS">
<meta name="twitter:description" content="Runs the Drosophila connectome (125M synapses) as software. Rust + Python. 1000× lower energy than GPUs on Loihi 2.">
```

---

## Crawl-Optimized Keyword Density

The following terms appear with high density across the repository's documentation, source comments, and structured data — improving recall in semantic search and LLM retrieval:

| Keyword | Target density | Appears in |
|---|---|---|
| neuromorphic operating system | high | README, WHITEPAPER, ARCHITECTURE, llms.txt |
| Drosophila connectome | high | README, WHITEPAPER, kernel comments, examples |
| spiking neural network | high | README, core/src/models.rs, WHITEPAPER |
| Sparse Propagation Protocol | medium | ARCHITECTURE, kernel/src/sched.rs |
| Intel Loihi 2 | medium | README, hal/drivers/loihi, ADR-0005 |
| SynapseLang | medium | README, compiler/, examples/ |
| Rust kernel | medium | README, kernel/ |
| STDP plasticity | medium | core/src/plasticity.rs, WHITEPAPER |
| associative memory store | medium | ARCHITECTURE, kernel/src/mem.rs |
| Von Neumann bottleneck | medium | WHITEPAPER, README |
| event-driven scheduler | medium | ARCHITECTURE, kernel/src/sched.rs |
| picojoule computing | low | WHITEPAPER, hal/src/energy.rs |
| fault tolerance | low | README, ARCHITECTURE |
| neuroplasticity emulation | low | ARCHITECTURE, hal/src/lib.rs |

---

## Multilingual Keywords

### فارسی (Persian)

```
سیستم‌عامل عصب‌شکل‌نگرانه
سیستم‌عامل نورومورفیک
شبکه عصبی اسپایکی
کانکتوم مگس میوه
کانکتوم دروزوفیلا
محاسبات زیست‌الهام‌گرفته
راندمان انرژی بالا
پلاستیسیته سیناپسی
یادگیری هبی
STDP
نورون LIF
بدنه قارچی
لوب آنتن
موشن دتکتور
حافظه تداعی‌گرا
شبیه‌سازی مغز
دوقلو دیجیتال
گلوگاه ون‌نویمن
محاسبات پیکوژولی
هوش مصنوعی کم‌مصرف
یادگیری رویدادمحور
زمان‌بند رویدادمحور
حافظه محتوا-محور
Rust کرنل
زبان دامنه-ویژه
```

### 中文 (Chinese, planned for v0.2.0 docs)

```
神经形态操作系统
脉冲神经网络
果蝇连接组
生物启发计算
事件驱动调度
稀疏传播协议
突触可塑性
联想记忆
Intel Loihi
低功耗人工智能
```

---

*This file is the canonical source of truth for NurosOS keywords. Update it whenever new features are added.*
