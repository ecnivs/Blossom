# Blossom
> SEAMLESS.INTELLIGENT.SECURE - Your Virtual Assistant

![swappy-20250213-101131](https://github.com/user-attachments/assets/d5bffa73-92b5-48e2-8e53-69e0f54f6dcd)

## 🏆 Recognition
> Secured **All India 4th Place** in **SmashHack 2024** under the name **Luna AI**

## Overview
This repository is dedicated to the software development of **Blossom**, a virtual assistant. The project aims to deliver a seamless and responsive user experience.

## Prerequisites
- Python 3.x (Tested with Python 3.11 using pyenv)
- Required Python libraries (listed in `requirements.txt`)
- [Large Language Model (LLM)](https://en.wikipedia.org/wiki/Large_language_model)
- [Ollama](https://ollama.com/)
- [Vosk model](https://alphacephei.com/vosk/models)

## Installation
1. Clone the repository:
```bash
git clone https://github.com/ecnivs/Blossom.git
```
2. Navigate to the project directory:
```bash
cd Blossom
```
3. Set up Python with pyenv:
```bash
pyenv install 3.11
pyenv local 3.11
```
4. Install dependencies:
```bash
pip install -r requirements.txt
```
5. Download an LLM:
```bash
ollama pull llama3.2:1b
```
6. Run the Software:
```bash
python main.py
```

## Configuration
1. **Vosk Model**: Download and place `vosk-model` in the directory.
2. **Ollama**: Enable Ollama
```bash
sudo systemctl enable ollama
```

## Contributing
We appreciate any feedback or code reviews! Feel free to:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Submit a pull request

### I'd appreciate any feedback or code reviews you might have!
