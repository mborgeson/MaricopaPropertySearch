# PostgreSQL Installation for Windows

1. Download PostgreSQL 14+ from: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
2. Run installer as Administrator
3. Installation settings:
   - Installation Directory: C:\Program Files\PostgreSQL\14
   - Data Directory: C:\Program Files\PostgreSQL\14\data
   - Password for postgres user: [REMEMBER THIS PASSWORD]
   - Port: 5433
   - Locale: English, United States
4. Finish installation (uncheck "Launch Stack Builder")
5. Add to PATH:
   - Open System Properties > Environment Variables
   - Edit System PATH
   - Add: C:\Program Files\PostgreSQL\14\bin
6. Verify installation:
   - Open new Command Prompt
   - Run: psql --version