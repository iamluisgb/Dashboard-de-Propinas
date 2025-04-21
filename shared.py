from pathlib import Path
import pandas as pd

# Define la ruta al directorio de la aplicación
app_dir = Path(__file__).parent

# Define la ruta al directorio de la aplicación
tips = pd.read_csv(app_dir / "tips.csv")
