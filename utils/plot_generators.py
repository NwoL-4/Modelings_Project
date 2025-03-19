import time


def generate_frame(subplots_data):
    """Генерирует фрейм для обновления субплотин

    Args:
        subplots_data: dict[tuple, dict]
            (row, col) -> {x: list, y: list, traces: list} 
    """
    frame = {
        'type': 'frame',
        'timestamp': time.time(),
        'subplots': []
    }

    for (row, col), data in subplots_data.items():
        frame['subplots'].append({
            'grid': {'row': row, 'col': col},
            'data': [
                {
                    'x': trace_data['x'],
                    'y': trace_data['y'],
                    'mode': trace_data.get('mode', 'lines'),
                    'name': trace_data.get('name')
                } for trace_data in data['traces']
            ],
            'layout': data.get('layout', {})
        })

    return frame
