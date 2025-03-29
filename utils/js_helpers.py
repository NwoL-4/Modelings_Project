import json
import os.path
from pathlib import Path

import plotly
from PySide6.QtCore import QObject, Signal, Slot

from constants import ui_constants as ui_constants
from core import abstract_classes as abstract_classes


class PythonJsBridge(QObject):
    """Мост для коммуникации между Python и JavaScript"""
    initFigJson = Signal(str)
    pushFrameJson = Signal(str, str)


    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self._ready = False
        self.logger = logger

    @Slot()
    def bridgeReady(self):
        """Вызывается когда JS мост готов"""
        self._ready = True
        self.logger.log("Мост активирован", abstract_classes.LogLevel.JS)

    @Slot(str)
    def logMessage(self, message):
        self.logger.log(f"{message}", abstract_classes.LogLevel.JS)

    @Slot(bool)
    def plotInitialized(self, success):
        """Callback после инициализации графика"""
        if success:
            self.logger.log(f"График инициализирован успешно", abstract_classes.LogLevel.JS)
        else:
            raise self.logger.log(f'График не был инициализирован', abstract_classes.LogLevel.JS)

    def init_plot(self, fig, webview):
        """
        Инициализация графика из plotly.Figure

        Args:
            fig (plotly.graph_objects.Figure): объект графика
            webview (): объект webviewwrapper
        """

        fig_json = json.dumps({
            'data': fig.data,
            'layout': fig.layout
        }, cls=plotly.utils.PlotlyJSONEncoder)
        # webview.page().runJavaScript(f"initializePlot('{fig_json}')")
        self.initFigJson.emit(fig_json)

    def add_frame(self, frame, slider, webview):
        """
        Добавление фрейма

        Args:
            frame (plotly.graph_objects.Frame): объект фрейма
            slider (list)
            webview (): объект webviewwrapper
        """

        frame_json = json.dumps(frame, cls=plotly.utils.PlotlyJSONEncoder)
        slider_json = json.dumps(slider, cls=plotly.utils.PlotlyJSONEncoder)
        # webview.page().runJavaScript(f"addFrame('{frame_json}', '{slider_json}')")
        self.pushFrameJson.emit(frame_json, slider_json)

def generate_html_code():
    main_path = os.path.join(Path(os.path.abspath(__file__)).parent.parent)

    return f"""
<!DOCTYPE html>
<html>
<head>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script src="{main_path}/src/plotly-3.0.1.min.js"></script>
    <style>
        #graph {{
            width: 100%;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div id="graph"></div>

    <script>
        // Глобальное состояние
        window.plotState = {{
            figure: null,
            bridge: null,
            frames: [],
        }};
        
        const config = {{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
        }};

        // Инициализация моста
        new QWebChannel(qt.webChannelTransport, function(channel) {{
            window.plotState.bridge = channel.objects.bridge;
            console.log("Bridge initialized");
            
            // Сообщаем Python, что мост готов
            if (window.plotState.bridge) {{
                window.plotState.bridge.initFigJson.connect(initializePlot);
                window.plotState.bridge.pushFrameJson.connect(addFrame);
                window.plotState.bridge.bridgeReady();
            }}
        }});

        window.plotState.bridge.logMessage('Ага');

        function initializePlot(plotJSON) {{
            const figure = JSON.parse(plotJSON);

            Plotly.react('graph', figure.data, figure.layout, config).then(() => {{
                window.plotState.figure = figure;
                window.plotState.figure.layout.sliders = [];
                window.plotState.figure.layout.sliders.push({{
                    steps: [],
                }});
                window.plotState.figure.frames = [];
                window.plotState.bridge.plotInitialized(true);
            }}).catch(error => {{
                console.error("Plot initialization error:", error);
                window.plotState.bridge.plotInitialized(false);
            }});
        }}

        function addFrame(frameJSON, sliderJSON) {{
            const frame = JSON.parse(frameJSON);
            const slider = JSON.parse(sliderJSON);
            
            window.plotState.figure.frames.push(frame);
            window.plotState.figure.layout.sliders[0].steps.push(slider);
            
            // Добавляем фреймы к текущему графику
            Plotly.react('graph', window.plotState.figure).then(() => {{
                window.plotState.bridge.logMessage('Фрейма добавлен успешно')
            }}).catch(error => {{
                window.plotState.bridge.logMessage('Фрейм не добавлен')
            }});
        }}

    </script>
</body>
</html>
"""


js_script = f'''
const layout = 
'''