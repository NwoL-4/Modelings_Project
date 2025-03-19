import json
import time

from PySide6.QtCore import QObject, Signal, Slot


class PythonJsBridge(QObject):
    initPlot = Signal(dict)  # Инициализация нового графика
    updatePlot = Signal(dict)  # Обновление данных
    logMessage = Signal(dict)  # Новый сигнал для логов

    def __init__(self):
        super().__init__()
        self.current_plots = {}

    @Slot(dict)
    def handle_js_log(self, log_data):
        """Обработчик логов из JS"""
        level = log_data.get('level', 'DEBUG').upper()
        message = log_data.get('message', '')
        context = log_data.get('context', {})

        log_entry = f"[JS {level}] {message}"
        if context:
            log_entry += f" | {json.dumps(context)}"

        print(log_entry)  # Или запись в файл

    @Slot(str, dict)
    def create_plot(self, plot_id, config):
        """Создание/обновление графика"""
        self.current_plots[plot_id] = config
        self.initPlot.emit({'id': plot_id, **config})

    @Slot(str, list)
    def add_frame(self, plot_id, traces):
        """Добавление кадра данных"""
        self.updatePlot.emit({
            'id': plot_id,
            'traces': traces,
            'timestamp': time.time()
        })


def generate_html_code():
    return """
<!DOCTYPE html>
<html>
<head>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script src="../src/plotly.min.js"></script>
</head>
<body>
    <div id="plotContainer" style="width:100%;height:100%"></div>

    <script>
        class JsLogger {
            constructor() {
                this.levels = ['DEBUG', 'INFO', 'WARN', 'ERROR']
                this.history = []
            }
        
            log(level, message, context = {}) {
                const entry = {
                    timestamp: new Date().toISOString(),
                    level: level.toUpperCase(),
                    message,
                    context
                }
                
                this.history.push(entry)
                window.pyBridge.logMessage(entry)
                
                // Сохранение оригинального console.log
                const original = console[level] || console.log
                original.apply(console, [`[${level}]`, message, context])
            }
        
            setupGlobalHandlers() {
                // Перехват ошибок
                window.onerror = (msg, url, line, col, error) => {
                    this.log('error', msg, {
                        url, line, col,
                        stack: error?.stack
                    })
                }
        
                // Перехват console
                this.levels.forEach(level => {
                    const original = console[level]
                    console[level] = (...args) => {
                        this.log(level, args.join(' '))
                        original.apply(console, args)
                    }
                })
            }
        }
        
        // Интеграция с Plotly
        function wrapPlotlyCalls() {
            const originalNewPlot = Plotly.newPlot
            Plotly.newPlot = function(container, data, layout, config) {
                try {
                    logger.log('debug', 'Plotly.newPlot initiated', {
                        container: container.id,
                        dataTypes: data.map(d => d.type),
                        layoutKeys: Object.keys(layout)
                    })
                    
                    return originalNewPlot.apply(this, arguments)
                        .then(() => {
                            logger.log('info', 'Plot initialized successfully', {
                                container: container.id
                            })
                        })
                        .catch(error => {
                            logger.log('error', 'Plot initialization failed', {
                                error: error.toString(),
                                stack: error.stack
                            })
                            throw error
                        })
                } catch (e) {
                    logger.log('error', 'Critical error in Plotly.newPlot', {
                        error: e.toString()
                    })
                }
            }
        }

        class PlotManager {
            constructor() {
                this.logger = new JsLogger()
                this.logger.setupGlobalHandlers()
                wrapPlotlyCalls()
                
                // Проверка наличия зависимостей
                this.logger.log('debug', 'Initializing PlotManager', {
                    dependencies: {
                        Plotly: typeof Plotly,
                        QWebChannel: typeof QWebChannel
                    }
                })
            }
            
            handleInit(msg) {
                if (!msg.id) {
                    this.logger.log('error', 'Missing plot ID in init message', {message: msg})
                    return
                }

            initWebChannel() {
                new QWebChannel(qt.webChannelTransport, channel => {
                    window.bridge = channel.objects.bridge;
                    this.setupSignals();
                });
            }

            setupSignals() {
                window.bridge.initPlot.connect(msg => this.handleInit(msg));
                window.bridge.updatePlot.connect(msg => this.handleUpdate(msg));
            }

            handleInit({id, type, layout, traces, config}) {
                const container = document.createElement('div');
                container.id = `plot-${id}`;
                document.body.appendChild(container);
                
                this.plots.set(id, {
                    type: type || 'scatter',
                    layout: {
                        ...layout,
                        autosize: true,
                        margin: {t: 40, b: 40, l: 60, r: 30}
                    },
                    config: {
                        responsive: true,
                        ...config
                    },
                    data: []
                });

                Plotly.newPlot(container, [], this.plots.get(id).layout, this.plots.get(id).config);
            }

            handleUpdate({id, traces}) {
                if (!this.plots.has(id)) return;

                const plot = this.plots.get(id);
                const updates = [];
                
                traces.forEach((trace, idx) => {
                    const fullTrace = {
                        type: plot.type,
                        mode: 'markers',
                        ...trace,
                        xaxis: 'x',
                        yaxis: 'y',
                        scene: plot.type.includes('3d') ? 'scene' : null
                    };
                    
                    if (idx < plot.data.length) {
                        updates.push({...fullTrace, ...{x: [trace.x], y: [trace.y], z: [trace.z]}});
                    } else {
                        plot.data.push(fullTrace);
                        Plotly.addTraces(`plot-${id}`, fullTrace);
                    }
                });

                if (updates.length > 0) {
                    Plotly.restyle(`plot-${id}`, updates);
                }

                // Автомасштабирование для 3D
                if (plot.type === 'scatter3d') {
                    Plotly.relayout(`plot-${id}`, {
                        scene: {
                            aspectmode: 'data'
                        }
                    });
                }
            }
        }

        // Инициализация после загрузки
        window.addEventListener('load', () => {
            window.plotManager = new PlotManager();
        });
    </script>
</body>
</html>
"""
