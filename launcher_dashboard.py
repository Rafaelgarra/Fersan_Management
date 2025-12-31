import sys
import os
from streamlit.web import cli as stcli

def resolve_path(path):
    if getattr(sys, 'frozen', False):
        # Se estiver compilado, busca na pasta temporária do PyInstaller
        base_path = sys._MEIPASS
    else:
        # Se estiver rodando script, busca na pasta atual
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, path)

if __name__ == "__main__":
    # Caminho para o seu arquivo de dashboard
    dashboard_path = resolve_path(os.path.join("dashboard", "dashboard_fluxo.py"))
    
    # Simula o comando "streamlit run dashboard/dashboard_fluxo.py"
    sys.argv = [
        "streamlit",
        "run",
        dashboard_path,
        "--global.developmentMode=false",
        "--server.headless=true"
    ]
    
    sys.exit(stcli.main())