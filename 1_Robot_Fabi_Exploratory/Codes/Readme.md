
# RobotFault AI Server for IoT

Distributed Systems project in Python using **TCP/IP Socket API**, multithreading and Machine Learning for predictive maintenance of industrial robots.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Correct Protocol Names](#2-correct-protocol-names)
  - [2.1 TCP/IP](#21-tcpip)
  - [2.2 UDP](#22-udp)
- [3. Project Objectives](#3-project-objectives)
- [4. System Architecture](#4-system-architecture)
  - [4.1 Server Data Flow](#41-server-data-flow)
  - [4.2 Mermaid Diagram](#42-mermaid-diagram)
- [5. Machine Learning Model](#5-machine-learning-model)
- [6. Robustness and Reliability](#6-robustness-and-reliability)
  - [6.1 Server-side Robustness](#61-server-side-robustness)
  - [6.2 Client-side Robustness](#62-client-side-robustness)
- [7. Lock Explanation](#7-lock-explanation)
- [8. Pickle and Pickle Check](#8-pickle-and-pickle-check)
- [9. Model File Versioning](#9-model-file-versioning)
- [10. Repository Structure](#10-repository-structure)
- [11. Installation and Execution (Linux / macOS)](#11-installation-and-execution-linux--macos)
- [12. Uploading the Project to GitHub](#12-uploading-the-project-to-github)
- [13. Source Code](#13-source-code)
- [14. How the Project Matches the Briefing](#14-how-the-project-matches-the-briefing)
- [15. Presentation Script](#15-presentation-script)
- [16. GitHub Repository Metadata](#16-github-repository-metadata)
- [17. Author](#17-author)

---

## 1. Overview

This project was developed for the **Distributed Systems – Integrative Project** course in an **Industry 4.0 predictive maintenance** context. The scenario describes a company that operates many high-precision industrial robots, where every minute of downtime is extremely expensive.

The goal is to **centralize intelligence**: instead of running AI locally on each robot, the robots send sensor or telemetry data through a **TCP/IP** network to a central server, which performs Machine Learning inference and returns a diagnosis in milliseconds.

The project focuses on three core requirements: handling multiple simultaneous connections with **threads**, performing **accurate diagnosis** with a server-side classifier, and preserving **managerial integrity** by preventing loss of alert counts due to synchronization failures such as **race conditions**.

---

## 2. Correct Protocol Names

Some preliminary notes may contain typos such as “ITC/IP” or “UDB”. The correct technical names are **TCP/IP** and **UDP**.

### 2.1 TCP/IP

**TCP/IP** stands for **Transmission Control Protocol / Internet Protocol**. TCP provides reliable, connection-oriented and ordered communication, while IP is responsible for addressing and routing across the network.

This project uses **TCP sockets** because the assignment explicitly requests TCP connection establishment between the robot client and the central server, and because reliability is required for counting alerts correctly.

### 2.2 UDP

**UDP** stands for **User Datagram Protocol**. It is lighter and often faster, but it does not guarantee packet delivery or packet ordering.

Although UDP can be useful in some real IoT environments, this academic implementation uses **TCP/IP** because reliability is more important for the classroom demonstration and because TCP is the protocol specified in the briefing.

---

## 3. Project Objectives

- Implement a **distributed client-server architecture** using the **Socket API** and **TCP/IP**.
- Create the robot client in `no_sensor.py`.
- Create the central server in `servidor_central.py`.
- Handle multiple simultaneous client connections with **threads**.
- Load a Machine Learning model from a `.pkl` file and perform inference in real time.
- Use `threading.Lock()` to protect the global alert counter from race conditions.
- Demonstrate the system with **3 robots connected in separate terminals**.

---

## 4. System Architecture

### 4.1 Server Data Flow

The server-side processing follows this workflow:

1. **Reception:** the network thread receives a string or JSON message from the robot with sensor or telemetry data.  
2. **Preprocessing:** the values are converted to numeric format and organized in an array such as `[[45.2, 0.8, 1200]]`.  
3. **Inference:** the loaded Machine Learning model in memory executes `.predict()` on the array and returns a class label.  
4. **Action:** if the model predicts failure, the thread increments the global alert counter using a **Lock** and sends the result back to the robot.

### 4.2 Mermaid Diagram

```mermaid
flowchart LR
    R1[Robot 1 - TCP Client]
    R2[Robot 2 - TCP Client]
    R3[Robot 3 - TCP Client]

    S[Central TCP/IP Server]

    T1[Thread 1]
    T2[Thread 2]
    T3[Thread 3]

    P[Preprocessing\nJSON -> float -> NumPy]
    M[ML Model\nRandom Forest .pkl]
    L[threading.Lock()]
    C[Global Alert Counter]
    D[Diagnosis Response\nNORMAL or FAILURE]

    R1 --> S
    R2 --> S
    R3 --> S

    S --> T1
    S --> T2
    S --> T3

    T1 --> P
    T2 --> P
    T3 --> P

    P --> M
    M --> D
    M --> L
    L --> C
```

---

## 5. Machine Learning Model

The AI component on the server works as a **State Classifier**, receiving a vector of features sent by the robot and returning a class label that represents the operating condition of the machine.

For this implementation, the chosen model is a **Random Forest Classifier**, because it is well suited for tabular numeric data, easy to train, and easy to save and load through a `.pkl` file.

### Input features

Depending on the stage of the project, example features include:

- `temperatura`
- `vibracao`
- `rpm`
- or higher-level telemetry such as `uptime_horas`, `latencia_ms`, `uso_cpu_pct`, `erros_api_por_minuto`, `versao_firmware`.

### Output labels

- `0` = NORMAL  
- `1` = FAILURE

---

## 6. Robustness and Reliability

To make the system more professional and more stable during the final demonstration, robustness improvements were added to both the server and the robot client while preserving the architecture requested in the briefing.

### 6.1 Server-side Robustness

The central server includes:

- logs indicating clients and actions, which helps explain which robot is connected and how each thread behaves during the demonstration.
- validation of incoming messages, preventing malformed payloads from breaking the thread.
- validation of required fields used in the model input, matching the preprocessing step.
- safe conversion of values to numeric types before inference.
- exception handling during inference, so one bad request does not stop the whole server, which is important because the system must support multiple simultaneous network flows.
- a global alert counter protected with `threading.Lock()`, preventing race conditions and preserving the integrity of the dashboard count.

### 6.2 Client-side Robustness

The improved robot client includes:

- clearer logs for each robot, making the demonstration easier to follow.
- handling of connectivity issues such as connection refused and server downtime.
- safe parsing of server responses, including error messages returned by the server.
- clearer display of sent sensor data and received diagnoses, which helps during the live demo with 3 terminals.

These changes improve reliability without changing the core client-server logic required by the assignment.

---

## 7. Lock Explanation

The project uses `threading.Lock()` to protect a global alert counter, because the server is multithreaded and each robot connection is handled by a separate thread.

Without a Lock, two or more threads could try to increment the counter at the same time, which could result in a **race condition** and lost alert counts.

### Short explanation for presentation

> The Lock was used to protect the global alert counter. Since each robot is handled by a different thread, two threads could try to update the counter at the same time. The Lock guarantees mutual exclusion, avoids race conditions, and ensures that no alert count is lost.

---

## 8. Pickle and Pickle Check

The trained Machine Learning model is stored in a `.pkl` file, which is loaded by the server before it starts accepting TCP connections.

A **pickle check** can be added before server startup to make the project safer and more professional by verifying that the `.pkl` file exists, loads correctly, and exposes a `.predict()` method.

This prevents the server from starting in an invalid state and helps guarantee that inference will work properly when the robots begin to send data.

### Short explanation for presentation

> Before the server starts, we can perform a pickle check. The system verifies whether the `.pkl` file exists, whether it is valid, and whether the loaded object supports `.predict()`. This guarantees that the AI model is ready for real-time inference before any robot connects.

---

## 9. Model File Versioning

The repository may include the file `modelo_falha_rf.pkl` so the project can run immediately after cloning, without requiring anyone to retrain the model first.

In larger production environments, binary model files are often excluded from version control, but in this academic project keeping the trained model in the repository improves reproducibility and simplifies the final demonstration.

---

## 10. Repository Structure

```bash
robotfault-ai-server-iot-distributed-system/
├── README.md
├── .gitignore
├── requirements.txt
├── servidor_central.py
├── no_sensor.py
├── treinar_modelo.py
├── modelo_falha_rf.pkl
└── exemplo_dados.csv
```

This layout keeps the central server, robot client, training script and serialized model/dataset in a single, easy-to-run folder.

---

## 11. Installation and Execution (Linux / macOS)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/robotfault-ai-server-iot-distributed-system.git
cd robotfault-ai-server-iot-distributed-system
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Train the model

```bash
python3 treinar_modelo.py
```

This step generates:

- `modelo_falha_rf.pkl`
- `exemplo_dados.csv`

### 5. Start the central server

```bash
python3 servidor_central.py
```

### 6. Start 3 robot clients in separate terminals

```bash
python3 no_sensor.py
```

Run `no_sensor.py` in three different terminals to satisfy the demonstration requirement of connecting **3 robots** and showing classification plus correct counter updates.

---

## 12. Uploading the Project to GitHub

To keep the repository organized and easy to run, the project files should be saved in the root of the repository with the correct extensions.

### Recommended file structure

```bash
robotfault-ai-server-iot-distributed-system/
├── README.md
├── .gitignore
├── requirements.txt
├── servidor_central.py
├── no_sensor.py
├── treinar_modelo.py
├── modelo_falha_rf.pkl
└── exemplo_dados.csv
```

### Correct file extensions

- `.py` → Python source code  
- `.md` → project documentation  
- `.txt` → dependency list  
- `.pkl` → trained Machine Learning model  
- `.csv` → example dataset  
- `.gitignore` → Git ignore rules file with no extension  

### Files that must be uploaded

The main files that should be uploaded to GitHub are:

- `README.md`
- `.gitignore`
- `requirements.txt`
- `servidor_central.py`
- `no_sensor.py`
- `treinar_modelo.py`

After running the training script locally, the following generated files can also be uploaded:

- `modelo_falha_rf.pkl`
- `exemplo_dados.csv`

Keeping `modelo_falha_rf.pkl` in the repository is useful in this academic project because the server must load a `.pkl` model directly and execute `.predict()` during the demonstration.

### Important note about `.gitignore`

If you want to upload the trained model file, do **not** add `*.pkl` to `.gitignore`.

### How to upload using the GitHub website

1. Create a new repository on GitHub.  
2. Open the repository page.  
3. Click **Add file**.  
4. Click **Upload files**.  
5. Drag and drop the project files or select them manually.  
6. Add a commit message.  
7. Click **Commit changes**.  

### How to upload using Git in the terminal

```bash
git init
git add .
git commit -m "Initial commit - RobotFault AI Server project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/robotfault-ai-server-iot-distributed-system.git
git push -u origin main
```

### Recommended local workflow before upload

1. Save all source files with the correct names and extensions.  
2. Run the training script:

```bash
python3 treinar_modelo.py
```

3. Confirm that the following files were generated:

- `modelo_falha_rf.pkl`
- `exemplo_dados.csv`

4. Test the server:

```bash
python3 servidor_central.py
```

5. Test the robot client in another terminal:

```bash
python3 no_sensor.py
```

6. After confirming everything works, upload the full project to GitHub.

This organization makes the repository easier to understand, easier to execute, and more suitable for the final class presentation with 3 robot terminals and a central AI server.

---

## 13. Source Code

### 13.1 `servidor_central.py`

The central server:

- accepts TCP connections,
- starts one thread per client,
- preprocesses sensor or telemetry data,
- loads the model from `.pkl`,
- executes `.predict()`,
- updates the shared alert counter using `Lock`,
- and sends the diagnosis back to the robot.

### 13.2 `no_sensor.py`

The robot client:

- connects to the TCP server,
- generates sensor values,
- sends them as JSON or delimited strings,
- receives the diagnosis,
- and displays the result in the terminal.

### 13.3 `treinar_modelo.py`

The training script:

- builds a simple tabular dataset,
- trains a Random Forest classifier,
- exports the dataset to CSV,
- and saves the final model as `modelo_falha_rf.pkl`.

### 13.4 `requirements.txt`

Suggested dependencies:

```txt
numpy
pandas
scikit-learn
joblib
```

---

## 14. How the Project Matches the Briefing

This implementation follows the development roadmap required in the briefing:

- **Activity 1:** connection establishment using **TCP sockets** with `no_sensor.py` and `servidor_central.py`.  
- **Activity 2:** creation of a **concurrent multithreaded server**, where each connection creates a new thread.  
- **Activity 3:** **real-time inference** by loading a `.pkl` model and calling `.predict()` inside the server thread.  
- **Activity 4:** synchronization of the alert dashboard using `threading.Lock()` to ensure counting precision.  
- **Final presentation:** demonstration with **3 robots** connected in different terminals while the server classifies data and updates the counter without errors.

---

## 15. Presentation Script

### Demonstration

Show:

- one terminal running `servidor_central.py`;
- three terminals running `no_sensor.py`;
- incoming robot data;
- diagnosis results;
- the alert counter increasing correctly when failure is detected.

### Network explanation

Explain that:

- **TCP/IP** was chosen because it offers reliable and ordered communication, which is important for not losing diagnostic messages or alert increments.  
- **Threads** guarantee that one robot does not block the others, so the server can keep serving the factory network continuously.

### Lock explanation

Use this short version:

> The Lock protects the shared alert counter. Since each client is handled by a separate thread, simultaneous updates could create race conditions. With the Lock, only one thread updates the counter at a time, so the dashboard count stays correct.

### Pickle explanation

Use this short version:

> The pickle file stores the trained Machine Learning model. Before the server starts, we validate the `.pkl` file to make sure it exists, loads correctly, and supports `.predict()`. That guarantees the model is ready for inference before robots begin sending data.

### Prompt Engineering

Explain that tools such as Gemini or ChatGPT helped integrate:

- the TCP client-server architecture,
- the multithreaded logic,
- and the Machine Learning inference pipeline into a single working solution.

---

## 16. GitHub Repository Metadata

**Repository name:**  
`robotfault-ai-server-iot-distributed-system`

**About:**  
Distributed system in Python with TCP/IP sockets, threads and Machine Learning for predictive maintenance in industrial robots.

**Topics / Tags:**

- `robotics`
- `predictive-maintenance`
- `industry40`
- `iot`
- `tcp-ip`
- `distributed-systems`
- `socket-programming`
- `multithreading`
- `machine-learning`
- `python`

---

## 17. Author

Academic project for the **Distributed Systems – Integrative Project** course.

Professor: **Carlos Eduardo Paes**.
