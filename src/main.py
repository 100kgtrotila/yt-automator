from src.infrastructure.ioc_container import Container
from src.presentation.main_window import MainApp

if __name__ == "__main__":
    container = Container()

    app = MainApp(container)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()