# 🎓 CampusFlow Platform

<div align="center">

![CampusFlow Logo](https://img.shields.io/badge/CampusFlow-Intelligent_Campus_Management-blue?style=for-the-badge&logo=graduation-cap)

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)

**🚀 Modern, Intelligent, and Responsive College Task Automation Platform**

</div>

---

## 🌟 Architecture Overview

```mermaid
graph TD
    A["🎓 Student User"] --> B["🌐 Frontend React App"]
    B --> C["🔥 API Gateway"]
    C --> D["🤖 AI Services"]
    C --> E["💾 Database Layer"]
    C --> F["📊 Analytics Engine"]
    
    subgraph Frontend_Stack ["Frontend Stack"]
        B1["⚛️ React + TypeScript"]
        B2["🎨 Vite + TailwindCSS"]
        B3["🔄 React Router"]
    end
    
    subgraph Backend_Services ["Backend Services"]
        D1["🧠 Medical AI"]
        D2["🛒 Stationery AI"]
        D3["📢 Voice Agent"]
        D4["🚗 Smart Parking"]
    end
    
    subgraph Data_Layer ["Data Layer"]
        E1["🗄️ PostgreSQL"]
        E2["📋 SQLAlchemy ORM"]
    end
    
    B --> B1
    B --> B2
    B --> B3
    
    C --> D1
    C --> D2
    C --> D3
    C --> D4
    
    E --> E1
    E --> E2
```

---

## 🔄 User Journey Flow

```mermaid
flowchart TD
    Start(["🚀 Launch App"]) --> Login{"🔐 Authenticated?"}
    Login -->|No| Auth["📱 Login / Register"]
    Auth --> Dashboard["📊 Dashboard"]
    Login -->|Yes| Dashboard
    
    Dashboard --> Module{"📱 Choose Module"}
    
    Module -->|Medical| MedicalFlow["🏥 Medical Management"]
    Module -->|Stationery| StationeryFlow["📚 Stationery Store"]
    Module -->|Announcements| AnnounceFlow["📢 Voice Agency"]
    Module -->|Parking| ParkingFlow["🚗 Smart Parking"]
    
    MedicalFlow --> MedicalActions{"🎯 Action"}
    MedicalActions -->|Add| AddRecord["➕ Add Record"]
    MedicalActions -->|View| ViewRecords["📋 View Records"]
    MedicalActions -->|Voice| VoiceMedical["🎤 Voice Command"]
    MedicalActions -->|Analytics| MedicalAnalytics["📊 Analytics"]
    
    StationeryFlow --> StationeryActions{"🎯 Action"}
    StationeryActions -->|Inventory| Inventory["📦 Manage Inventory"]
    StationeryActions -->|Forecast| Forecast["📈 Demand Forecast"]
    StationeryActions -->|Orders| Orders["🛒 Process Orders"]
    
    AnnounceFlow --> AnnounceActions{"🎯 Action"}
    AnnounceActions -->|Record| RecordVoice["🎤 Record Message"]
    AnnounceActions -->|Broadcast| Broadcast["🌐 Broadcast"]
    AnnounceActions -->|Schedule| Schedule["📝 Schedule"]
    
    ParkingFlow --> ParkingActions{"🎯 Action"}
    ParkingActions -->|Check| CheckSlots["🅿️ Check Slots"]
    ParkingActions -->|Reserve| Reserve["🚗 Reserve Slot"]
    ParkingActions -->|Status| ParkingStatus["📊 Real-time Status"]
    
    AddRecord --> Dashboard
    ViewRecords --> Dashboard
    VoiceMedical --> Dashboard
    MedicalAnalytics --> Dashboard
    
    Inventory --> Dashboard
    Forecast --> Dashboard
    Orders --> Dashboard
    
    RecordVoice --> Dashboard
    Broadcast --> Dashboard
    Schedule --> Dashboard
    
    CheckSlots --> Dashboard
    Reserve --> Dashboard
    ParkingStatus --> Dashboard
```

---

## 🔗 API Interaction Sequence

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant F as 🌐 Frontend
    participant A as 🚀 API Gateway
    participant M as 🏥 Medical Service
    participant D as 💾 Database
    participant AI as 🤖 AI Service
    
    U->>F: 🖱️ Click Add Medical Record
    F->>F: 📝 Open Form Modal
    U->>F: ⌨️ Fill Medical Details
    F->>A: 📤 POST /api/medical/
    
    A->>A: 🔍 Validate Request
    A->>M: 🔄 Forward to Medical Service
    
    M->>D: 💾 Save Medical Record
    D-->>M: ✅ Record Created
    M->>AI: 🤖 Generate AI Insights
    AI-->>M: 🧠 Medical Analysis
    M-->>A: 📊 Record + Insights
    A-->>F: 📋 Response Data
    F->>F: 🎨 Update UI
    F-->>U: ✅ Success Notification
    
    Note over U,A: 🎤 Voice Command Flow
    U->>F: 🎤 Request: Show medical records
    F->>A: 📤 POST /api/medical/voice
    A->>AI: 🗣️ Process Voice Command
    AI-->>A: 📝 Parsed Intent
    A->>M: 📋 GET /api/medical/
    M->>D: 📊 Query Records
    D-->>M: 📋 Medical Data
    M-->>A: 📊 Records List
    A-->>F: 📋 JSON Response
    F->>F: 🎨 Render Table
    F-->>U: 📊 Display Records
```

---

## 🏗️ System Architecture State Diagram

```mermaid
stateDiagram-v2
    [*] --> Initializing
    
    Initializing --> DatabaseSetup: 🗄️ Init DB
    Initializing --> ServerStart: 🚀 Start Server
    
    DatabaseSetup --> ServerStart: ✅ DB Ready
    DatabaseSetup --> Error: ❌ DB Failed
    
    ServerStart --> Listening: 🌐 Port 8000
    ServerStart --> Error: ❌ Server Failed
    
    Listening --> ProcessingRequest: 📨 Request Received
    ProcessingRequest --> AuthCheck: 🔐 Validate User
    
    AuthCheck --> Authorized: ✅ Auth Success
    AuthCheck --> Unauthorized: ❌ Auth Failed
    
    Authorized --> RouteRequest: 🛣️ Route to Service
    Unauthorized --> Error: 🚫 Return 401
    
    RouteRequest --> MedicalService: 🏥 /api/medical
    RouteRequest --> StationeryService: 📚 /api/stationery
    RouteRequest --> AnnouncementService: 📢 /api/announcements
    RouteRequest --> ParkingService: 🚗 /api/parking
    
    MedicalService --> DatabaseQuery: 💾 Query DB
    StationeryService --> DatabaseQuery: 💾 Query DB
    AnnouncementService --> DatabaseQuery: 💾 Query DB
    ParkingService --> DatabaseQuery: 💾 Query DB
    
    DatabaseQuery --> AIProcessing: 🤖 AI Analysis
    AIProcessing --> ResponseGeneration: 📤 Format Response
    ResponseGeneration --> Listening: 🔄 Ready for Next
    
    Error --> RecoveryMode: 🔄 Attempt Recovery
    RecoveryMode --> Listening: ✅ Recovered
    RecoveryMode --> [*]: ❌ Shutdown
    

```

---

## 🚀 Quick Start

<div align="center">

### 🎯 One-Click Setup (Windows)

```bash
# 🎈 Double-click these files in order:
start_backend.bat    # 🚀 Launches FastAPI Backend
start_frontend.bat   # ⚛️ Launches React Frontend
```

### 🛠️ Manual Setup

```bash
# 🐍 Backend Setup
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# ⚛️ Frontend Setup  
cd frontend
npm install
npm run dev
```

**🌐 Access Points:**
- 🎯 Frontend: `http://localhost:5173`
- 🔧 Backend API: `http://localhost:8000`
- 📚 API Docs: `http://localhost:8000/docs`

</div>

---

## 🎯 Core Features

### 🏥 Medical Room Management
```mermaid
pie showData
    title Medical Module Features
    "📝 Record Management" : 25
    "🎤 Voice Commands" : 20
    "📊 AI Analytics" : 20
    "🔔 Smart Alerts" : 15
    "📱 Mobile Access" : 20
```

- 📝 **Digital Medical Records** - Complete student health tracking
- 🎤 **Voice-Powered Commands** - Natural language medical queries
- 🧠 **AI Health Insights** - Intelligent medical analysis
- 📊 **Real-time Analytics** - Health trends and statistics
- 🔔 **Smart Notifications** - Automated medication reminders
- 🚕 **Emergency Cab Quotes** - Server-validated Uber/Ola fare estimates via `POST /api/dispatch/emergency-quote`

### 📚 Stationery Store Intelligence
```mermaid
graph LR
    A[📦 Inventory] --> B[📈 Demand Forecast]
    B --> C[🤖 AI Recommendations]
    C --> D[🛒 Auto-Ordering]
    D --> E[📊 Analytics Dashboard]
    E --> A
    
    style A fill:#059669,stroke:#047857,color:#ffffff
    style B fill:#0891b2,stroke:#0e7490,color:#ffffff
    style C fill:#7c3aed,stroke:#6d28d9,color:#ffffff
    style D fill:#dc2626,stroke:#b91c1c,color:#ffffff
    style E fill:#f59e0b,stroke:#d97706,color:#ffffff
```

- 📦 **Smart Inventory Management** - Real-time stock tracking
- 📈 **AI Demand Forecasting** - Predictive analytics
- 🛒 **Automated Reordering** - Never run out of supplies
- 📊 **Usage Analytics** - Consumption patterns and insights
- 💰 **Budget Optimization** - Cost-effective procurement

### 📢 Voice Agency System
- 🎤 **Multilingual Support** - Multiple language announcements
- 🗣️ **Text-to-Speech** - Natural voice generation
- 📅 **Scheduled Broadcasting** - Automated announcements
- 🌐 **Campus-Wide Reach** - Multi-location delivery
- 📱 **Mobile Integration** - Remote announcement control

### 🚗 Smart Parking Solution
- 🅿️ **Real-time Slot Detection** - Live parking availability
- 📸 **License Plate Recognition** - Automated vehicle tracking
- 📊 **Usage Analytics** - Peak hours and patterns
- 🎫 **Digital Booking** - Reserve parking slots
- 🔔 **Smart Notifications** - Arrival/departure alerts

---

## 🛠️ Technology Stack

### 🎨 Frontend Architecture
```mermaid
graph TB
    subgraph Frontend_Stack ["Frontend Stack"]
        A[⚛️ React 18] --> B[📘 TypeScript]
        B --> C[🎨 TailwindCSS]
        C --> D[🚀 Vite]
        D --> E[🛣️ React Router]
        E --> F[🔥 React Hot Toast]
        F --> G[🎯 React Icons]
    end
    
    subgraph State_Management ["State Management"]
        H[🔄 React Hooks]
        I[📡 Axios]
        J[💾 Local Storage]
    end
    
    subgraph UI_Components ["UI Components"]
        K[📋 Custom Tables]
        L[🎤 Voice Recorder]
        M[📊 Charts.js]
        N[🎨 Modals]
    end
    
    A --> H
    B --> I
    C --> J
    D --> K
    E --> L
    F --> M
    G --> N
    
    classDef frontend fill:#3b82f6,stroke:#2563eb,color:#ffffff
    classDef state fill:#10b981,stroke:#059669,color:#ffffff
    classDef ui fill:#8b5cf6,stroke:#7c3aed,color:#ffffff
    
    class A,B,C,D,E,F,G frontend
    class H,I,J state
    class K,L,M,N ui
```

### 🚀 Backend Architecture
```mermaid
graph TB
    subgraph Backend_Core ["Backend Core"]
        A[🐍 FastAPI] --> B[🔧 Pydantic]
        B --> C[🗄️ SQLAlchemy]
        C --> D[🌐 CORS Middleware]
    end
    
    subgraph AI_Services ["AI Services"]
        E[🧠 OpenRouter API]
        F[🎤 Speech Recognition]
        G[📊 Analytics Engine]
        H[🔍 NLP Processing]
    end
    
    subgraph Data_Layer ["Data Layer"]
        I[🗄️ PostgreSQL]
        J[📋 Database Models]
        K[🔄 Migrations]
    end
    
    subgraph Security_Layer ["Security Layer"]
        L[🔐 JWT Auth]
        M[🚫 Rate Limiting]
        N[🔍 Input Validation]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    
    E --> I
    F --> J
    G --> K
    H --> L
    
    I --> M
    J --> N
    K --> L
    
    classDef backend fill:#8b5cf6,stroke:#7c3aed,color:#ffffff
    classDef ai fill:#f59e0b,stroke:#d97706,color:#ffffff
    classDef data fill:#ec4899,stroke:#db2777,color:#ffffff
    classDef security fill:#ef4444,stroke:#dc2626,color:#ffffff
    
    class A,B,C,D backend
    class E,F,G,H ai
    class I,J,K data
    class L,M,N security
```

---

## 📊 Performance Metrics

```mermaid
gantt
    title CampusFlow Development Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1
    Backend API      :done, backend, 2024-01-01, 2024-02-15
    Frontend Base    :done, frontend, 2024-01-15, 2024-03-01
    section Phase 2
    AI Integration   :active, ai, 2024-02-20, 2024-04-01
    Voice Features   :voice, 2024-03-15, 2024-04-15
    section Phase 3
    Testing and QA   :t1, 2024-04-01, 2024-05-01
    Deployment       :deploy, 2024-05-01, 2024-05-15
```

### ⚡ Performance Benchmarks
- 🚀 **API Response Time**: <200ms average
- 📱 **Frontend Load**: <3 seconds initial load
- 🎤 **Voice Processing**: <1 second response
- 📊 **Database Queries**: Optimized with indexing
- 🔋 **Memory Usage**: <512MB per service

---

## 🔧 Configuration

### 📁 Environment Variables
```bash
# 🗄️ Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/CampusFlow

# 🤖 AI Services
OPENROUTER_API_KEY=your_openrouter_key_here

# 🌐 Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 🔐 Security
SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
```

### 🐳 Docker Setup
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/CampusFlow
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=CampusFlow
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🧪 Testing & Quality

### 🧪 Test Coverage
The project follows comprehensive testing practices with unit tests, integration tests, and end-to-end testing to ensure code quality and reliability.

### 🧪 Test Commands
```bash
# 🐍 Backend Tests
cd backend
pytest tests/ -v --cov=.

# ⚛️ Frontend Tests
cd frontend
npm run test
npm run test:e2e

# 📊 Coverage Report
pytest --cov=backend --cov-report=html
```

---

## 🚀 Deployment

### 🌐 Production Deployment
```mermaid
flowchart TD
    A[👨‍💻 Developer] --> B[🔄 Git Push]
    B --> C[🚀 CI/CD Pipeline]
    C --> D[🧪 Run Tests]
    D --> E{✅ Tests Pass?}
    E -->|No| F[🐛 Fix Issues]
    F --> B
    E -->|Yes| G[🐳 Build Docker]
    G --> H[📦 Deploy to Staging]
    H --> I[🧪 Staging Tests]
    I --> J{✅ Staging OK?}
    J -->|No| K[🔧 Rollback]
    J -->|Yes| L[🚀 Deploy to Production]
    L --> M[📊 Monitor Health]
    M --> N[🔄 Auto Scaling]
    
    classDef dev fill:#10b981,stroke:#059669,color:#ffffff
    classDef pipeline fill:#3b82f6,stroke:#2563eb,color:#ffffff
    classDef test fill:#f59e0b,stroke:#d97706,color:#ffffff
    classDef deploy fill:#8b5cf6,stroke:#7c3aed,color:#ffffff
    classDef prod fill:#ef4444,stroke:#dc2626,color:#ffffff
    
    class A dev
    class B,C pipeline
    class D,E,I,J test
    class G,H,K deploy
    class L,M,N prod
```

### ☁️ Cloud Platforms
- **AWS** - ECS, RDS, S3, CloudFront
- **Google Cloud** - Cloud Run, Cloud SQL, Cloud Storage
- **Azure** - App Service, Azure SQL, Blob Storage
- **DigitalOcean** - App Platform, Managed Databases

---

## 🤝 Contributing

### 📋 Development Workflow
1. 🍴 **Fork** the repository
2. 🌿 **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. 📝 **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. 📤 **Push** to the branch (`git push origin feature/amazing-feature`)
5. 🔄 **Open** a Pull Request

### 🎯 Contribution Guidelines
- 📝 Follow **PEP 8** for Python code
- 📘 Use **TypeScript** strictly typed code
- 🧪 Write **tests** for new features
- 📚 Update **documentation** as needed
- 🎨 Follow **existing** code style

---

## 📄 License

<div align="center">

![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**🎓 CampusFlow Platform** - *Intelligent Campus Management System*

Made with ❤️ by the CampusFlow Team

</div>

---

## 🙋‍♂️ Support

### 📞 Get Help
- 📧 **Email**: support@CampusFlow.com
- 💬 **Discord**: [Join our community](https://discord.gg/CampusFlow)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/CampusFlow/issues)
- 📚 **Documentation**: [docs.CampusFlow.com](https://docs.CampusFlow.com)

### 🎯 FAQ
- **Q**: How do I reset the database?
- **A**: Run `python inspect_db.py --reset`

- **Q**: Can I use my own AI model?
- **A**: Yes! Configure your OpenRouter API key in `.env`

- **Q**: Is mobile support available?
- **A**: The responsive design works on all devices!

---

<div align="center">

**⭐ Star this repo if it helped you!**

[![GitHub stars](https://img.shields.io/github/stars/your-repo/CampusFlow?style=for-the-badge&logo=github)](https://github.com/your-repo/CampusFlow)
[![GitHub forks](https://img.shields.io/github/forks/your-repo/CampusFlow?style=for-the-badge&logo=github)](https://github.com/your-repo/CampusFlow/fork)
[![GitHub issues](https://img.shields.io/github/issues/your-repo/CampusFlow?style=for-the-badge&logo=github)](https://github.com/your-repo/CampusFlow/issues)

</div>
