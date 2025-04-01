from setuptools import setup, find_packages

# Leer dependencias desde requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="voice-lead-agent",
    version="0.1.0",
    description="AI Agent de Voz para Nutrición de Leads",
    author="Tu Nombre",
    author_email="tu.email@ejemplo.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,  # Usar las dependencias del archivo requirements.txt
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    entry_points={
        "console_scripts": [
            "voice-agent=app.main:main",
        ],
    },
)