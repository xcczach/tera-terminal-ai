"""PyInstaller 入口脚本，避免相对导入问题。"""
from src.tera.cli import main

if __name__ == "__main__":
    main()