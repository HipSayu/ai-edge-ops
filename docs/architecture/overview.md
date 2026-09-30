# Architecture Overview

## 1. Overview

The platform follows a **Cloud–Edge architecture** that separates centralized management from distributed AI execution.

* **Cloud** acts as the **Control Plane**.
* **Edge** acts as the **Data Plane**.
* Cloud manages Edge Clusters, Nodes, deployments, configurations, and platform state.
* Edge Nodes execute AI workloads locally through containerized AI Runtimes.

## 2. High-Level Architecture

```mermaid
flowchart TB

    CLIENT["Client"]

    subgraph CLOUD["Cloud Control Plane"]
        CLOUD_SERVER["Cloud Server"]

        RDS["PostgreSQL"]
        REDIS["Redis"]
        S3["Object Storage"]
        ECR["Container Registry"]
        IOT["IoT / MQTT"]

        CLOUD_SERVER --> RDS
        CLOUD_SERVER --> REDIS
        CLOUD_SERVER --> S3
        CLOUD_SERVER --> ECR
        CLOUD_SERVER --> IOT
    end

    subgraph EDGE["Edge Data Plane"]
        subgraph CLUSTER["Edge Cluster"]
            NODE1["Edge Node"]
            NODE2["Edge Node"]
            NODEN["Edge Node"]

            NODE1 --> AGENT1["Edge Agent"]
            NODE2 --> AGENT2["Edge Agent"]
            NODEN --> AGENTN["Edge Agent"]
        end
    end

    CLIENT -->|HTTPS| CLOUD_SERVER

    IOT <-->|MQTT| AGENT1
    IOT <-->|MQTT| AGENT2
    IOT <-->|MQTT| AGENTN

    S3 -->|Model / Artifact| AGENT1
    ECR -->|Container Image| AGENT1

    S3 -->|Model / Artifact| AGENT2
    ECR -->|Container Image| AGENT2

    S3 -->|Model / Artifact| AGENTN
    ECR -->|Container Image| AGENTN
```

## 3. Architectural Hierarchy

The platform follows a hierarchical resource model:

```mermaid
flowchart TB

    CLOUD["Cloud"]

    CLUSTER1["Edge Cluster"]
    CLUSTERN["Edge Cluster"]

    NODE1["Edge Node"]
    NODE2["Edge Node"]
    NODEN["Edge Node"]

    AGENT1["Edge Agent"]
    AGENT2["Edge Agent"]
    AGENTN["Edge Agent"]

    RUNTIME1["AI Runtime"]
    RUNTIME2["AI Runtime"]
    RUNTIMEN["AI Runtime"]

    CLOUD --> CLUSTER1
    CLOUD --> CLUSTERN

    CLUSTER1 --> NODE1
    CLUSTER1 --> NODE2
    CLUSTER1 --> NODEN

    NODE1 --> AGENT1
    NODE2 --> AGENT2
    NODEN --> AGENTN

    AGENT1 --> RUNTIME1
    AGENT2 --> RUNTIME2
    AGENTN --> RUNTIMEN
```

The relationships are:

```text
Cloud
  └── Edge Cluster (1:N)
        └── Edge Node (1:N)
              └── Edge Agent (1:1)
                    └── AI Runtime (1:N)
```

## 4. Control Plane and Data Plane

```mermaid
flowchart LR

    subgraph CONTROL["Control Plane"]
        CS["Cloud Server"]
        STATE["Platform State"]
        DEPLOY["Deployment Management"]
        MONITOR["Monitoring"]
    end

    subgraph DATA["Data Plane"]
        AGENT["Edge Agent"]
        RUNTIME["AI Runtime"]
        DATA_SOURCE["Data Source"]
    end

    CS --> STATE
    CS --> DEPLOY
    CS --> MONITOR

    CS -->|Commands / Configuration| AGENT
    AGENT -->|Lifecycle Management| RUNTIME
    DATA_SOURCE --> RUNTIME
    RUNTIME -->|Telemetry / Events| AGENT
    AGENT -->|Telemetry / Status| CS
```

### Control Plane

The Cloud Control Plane is responsible for centralized management:

* Resource management
* Deployment management
* Configuration management
* Desired state
* Monitoring
* Edge coordination

### Data Plane

The Edge Data Plane is responsible for local execution:

* Data processing
* AI inference
* Runtime lifecycle
* Local resource utilization
* Telemetry collection

## 5. Main Architectural Components

| Component          | Responsibility                        |
| ------------------ | ------------------------------------- |
| Cloud Server       | Centralized platform management       |
| Edge Cluster       | Logical grouping of Edge Nodes        |
| Edge Node          | Edge computing resource               |
| Edge Agent         | Node-level control and reconciliation |
| AI Runtime         | AI workload execution                 |
| PostgreSQL         | Persistent platform state             |
| Redis              | Cache and temporary state             |
| Object Storage     | Models and artifacts                  |
| Container Registry | Runtime container images              |
| IoT / MQTT         | Cloud–Edge messaging                  |

## 6. Core Communication

The main communication paths are:

```mermaid
flowchart TB

    CLIENT["Client"]
    CLOUD["Cloud Server"]
    IOT["IoT / MQTT"]
    AGENT["Edge Agent"]
    RUNTIME["AI Runtime"]

    CLIENT -->|HTTPS| CLOUD

    CLOUD -->|Command| IOT
    IOT -->|MQTT| AGENT

    AGENT -->|Lifecycle Control| RUNTIME

    RUNTIME -->|Telemetry / Event| AGENT
    AGENT -->|MQTT| IOT
    IOT -->|Telemetry / Event| CLOUD
```

The architecture therefore separates:

**Client → Cloud → Edge Agent → AI Runtime**

for control and execution, while telemetry follows the reverse direction:

**AI Runtime → Edge Agent → Cloud**.
