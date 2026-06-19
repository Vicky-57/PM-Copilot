# Celery background task

def compile_csv_task(rows):
    print('Compiling CSV rows in background:', rows)
    return True
