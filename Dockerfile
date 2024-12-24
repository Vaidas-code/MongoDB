# Naudokite oficialų Python atvaizdą iš Docker Hub
FROM python:3.11

# Nustatykite darbo katalogą konteineryje
WORKDIR /app

# Nukopijuokite priklausomybių failą į konteinerį
COPY requirements.txt .

# Įdiekite priklausomybes
RUN pip install --no-cache-dir -r requirements.txt

# Nukopijuokite likusį darbo katalogo turinį į konteinerį
COPY . .

# Nurodykite komandą, kuri paleis aplikaciją
CMD ["python", "app.py"]
