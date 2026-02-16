# 💻 TechHub - Project Sharing and Q&A Platform

![Contributors](https://img.shields.io/github/contributors/x0rma-404/TechHub?style=for-the-badge&color=blue)
![Forks](https://img.shields.io/github/forks/x0rma-404/TechHub?style=for-the-badge&color=magenta)
![Stars](https://img.shields.io/github/stars/x0rma-404/TechHub?style=for-the-badge&color=yellow)

TechHub is a web‑based **Project Sharing and Q&A platform** where developers can share their projects, ask questions, exchange knowledge, and try out useful mini coding tools — kind of like a mini **GitHub + forum + coding sandbox**! ✨

---

## 🚀 Features

* 🤖 **Dastan AI Assistant**: Integrated Q&A bot that provides auto-answers, responds to mentions, and offers a dedicated AI chatbot interface.
* 🛠️ **Advanced Visualizers**: Interactive Binary Search Tree (BST) and Sorting Algorithm visualizers for better learning.
* 📌 Share your **projects** with descriptions, tech stack, and demo links.
* ❓ Ask questions and get answers from other developers.
* 🛠 Use **professional coding tools** with advanced UI/UX.
* 🔎 Browse projects with categories & filters.
* 👤 Track user activity with profiles & badges.
* ✨ **Premium UI**: Smooth 3D effects, staggered animations, and modern glassmorphism.
* 📱 Responsive design for both desktop and mobile.
* 🔗 **GitHub Integration**: Connect your GitHub account, import repositories as projects, and sync project details (stars, description) in real-time.
* 📂 **Project Management**: Create, view, and delete projects with specialized landing pages and sync status.


---

## 🧠 Built With

* **Python** with the **Flask** web framework
* **HTML, CSS, JavaScript** for frontend
* **Tailwind CSS** for modern styling
* **REST API** architecture
* **Ollama/Godbolt API** for AI and remote code execution

---

## 📦 Installation

You **do not need a virtual environment**; just install dependencies globally:

1. Clone the repository:
```bash
git clone https://github.com/x0rma-404/TechHub.git
cd TechHub
```

2. Install dependencies globally:

```bash
pip install -r requirements.txt
```

3. Install and run **Ollama** (required for Dastan AI):
   - Download from [ollama.com](https://ollama.com/)
   - Pull the required model:
     ```bash
     ollama pull llama3.2:3b
     ```

4. Run the server:

```bash
python app.py
```

### 🔐 Security Configuration

> [!WARNING]
> Before running in production, you **MUST** configure the following environment variables:
> - `FERNET_KEY`: Used for encrypting GitHub tokens. If not set, it generates a new key on startup, which will invalidate old tokens after restart.
> - `FLASK_SECRET_KEY`: Used for session security.

5. Open the app in your browser:


```
http://localhost:5000
```

---

## 🛠 Usage

* Register an account
* Login and ask or answer questions (Tag **@Dastan** for AI help!)
* Share your own projects
* Explore professional tools:

  * **Floating Point Converter**: IEEE-754 standard visualization (Decimal ↔ Binary)
  * **Python Visualizer**: Step-by-step code execution with variable tracing
  * **Logic Evaluator**: Real-time truth table generation and logical simplification (e.g., `!A` → `Ā`, `->` → `→`, `^` → `⊕`)
  * **Linux Simulator**: Browser-based persistent terminal simulation
  * **BST Visualizer**: Interactive Binary Search Tree visualization (Add/Search/Delete)
  * **Sorting Visualizer**: Real-time animation of sorting algorithms (Bubble, Merge, Quick, etc.)
  * **IP Subnet Calculator**: Network details and mask calculations
  * **CSV ↔ JSON Converter**: Professional data format transformation

## 🔗 GitHub Synchronization

* **Connect**: Securely link your GitHub account using a Personal Access Token (PAT).
* **Import**: Select any of your repositories to instantly create a TechHub project.
* **Sync**: Keep your project's stars, language, and description up-to-date with one click.
* **Direct Upload**: Upload code files directly to your repositories from the TechHub interface.


## 📟 Mini IDEs (Execution via Godbolt API):
  * **Python 3**
  * **C/C++ (GCC 14)**
  * **Java (JDK 23)**
  * **Ruby 3.3**
  * **Go 1.22**
  * Javascript (Coming Soon)

---

## 📈 Future Plans

* Real‑time messaging between users
* Advanced mini coding tools
* Analytics & trending project feeds
* Mobile‑friendly UI enhancements

---

## 📄 License

This project currently has **No License** — you can use and modify it freely.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to check the [issues page](https://github.com/x0rma-404/TechHub/issues).

### ✨ Contributors

A huge thanks to these amazing people who have contributed to TechHub:

<a href="https://github.com/x0rma-404/TechHub/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=x0rma-404/TechHub" />
</a>

---

## 🙌 Thanks

Thank you for exploring TechHub! Feel free to ⭐ the repo to show support.
