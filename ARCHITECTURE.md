1|# Architecture — Younify Distributed AI Inference System
2|
3|## Goal
4|
5|Build a distributed inference cluster where multiple machines pool their GPU/CPU compute to run one model collaboratively, without a job dispatch queue — workers auto-connect and contribute resources directly via llama.cpp RPC.
6|
7|---
8|
9|## System Architecture (Current State)
10|
11|```
12|┌──────────────────────────────────────────────────────────────────┐
13|│                        HEAD NODE                                 │
14|│                                                                  │
15|│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐ │
16|│  │  Redis        │     │  API Gateway      │     │  Coordinator  │ │
17|│  │  Port 6379    │◄────│  Port 3000        │     │  Port 8050    │ │
18|│  │               │     │  ┌────────────┐   │     │               │ │
19|│  │  Task Queue   │     │  │ Dashboard  │   │     │  Worker       │ │
20|│  │  Job Results  │     │  │ (SPA)      │   │     │  Registry     │ │
21|│  └──────────────┘     │  └────────────┘   │     │  Health        │ │
22|│          ▲            └──────────────────┘     │  Monitor       │ │
23|│          │                │                     └───────┬───────┘ │
24|│          │                │  LPUSH tasks                │         │
25|│          │                ▼                             │         │
26|│          │     ┌──────────────────┐                     │         │
27|│          └─────┤  Local Workers   │                     │         │
28|│                │  (Ollama)        │                     │         │
29|│                └──────────────────┘                     │         │
30|│                                                        │         │
31|│  ┌──────────────────────────────────────────────────────┐│         │
32|│  │  llama-server (port 8080)                            ││         │
33|│  │  Runs model with --rpc <worker1>:5000 --rpc <w2>:.. ││         │
34|│  │  llama.cpp distributes layers across all workers     ││         │
35|│  └────────────────────────┬─────────────────────────────┘│         │
36|│                           │                              │         │
37|└───────────────────────────┼──────────────────────────────┼─────────┘
38|                            │                              │
39|                     Tailscale Mesh VPN                    │
40|                            │                              │
41|┌───────────────────────────┼──────────────────────────────┼─────────┐
42|│                    WORKER NODE ┌─────────────────────────┘         │
43|│                               ▼                                    │
44|│  ┌────────────────────┐  ┌────────────────────────────────────┐   │
45|│  │  llama-rpc-server  │  │  cluster_worker.py                  │   │
46|│  │  Port 5000          │  │  Registers with coordinator        │   │
47|│  │                     │  │  Sends heartbeats every 10s        │   │
48|│  │  Contributes VRAM   │  │  Starts llama-rpc-server           │   │
49|│  │  to head node       │  │                                    │   │
50|│  └────────────────────┘  └────────────────────────────────────┘   │
51|└────────────────────────────────────────────────────────────────────┘
52|```