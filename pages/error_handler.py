def convert_type(string, typee):
    try:
        return typee(string)
    except:
        if typee.__name__ == 'float':
            raise ValueError(f'Значение должно быть типа {typee.__name__}. Вводить нужно через точку'
                             f'\nПример: 1.2')
        else:
            raise ValueError(f'Значение должно быть типа {typee.__name__}.')
