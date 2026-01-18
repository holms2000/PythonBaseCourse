'''
   The program must read the input file with the initial configuration of the field. File format 0 is not a live cell, 1 is a live cell. The number of simulation steps is set as 1 argument when calling the program. 
The program simulates a colony of organisms in accordance with the rules of the game of Life, writing each new configuration to the output file, as well as creating an image (snapshot) of the field state as a separate
PNG file. The PIL (Pillow) library is used to work with images.
The base color of the “live” cell must be set as 2 arguments when calling the program (it can only be a “pure color"). 
The program uses shades of this base color to indicate the “age" of the cell.v
'''
import csv
from PIL import Image, ImageDraw
import sys

# Параметры программы
GENERATIONS = int(sys.argv[1])  # Количество шагов моделирования [1]
BASE_COLOR = sys.argv [2] # Базовый цвет для живых клеток [2]
WIDTH = 0
HEIGHT = 0
INPUT_FILE = 'init.csv'                     #имя констант всегда заглавными буквами
OUTPUT_FILE_CSV = 'generation.csv'
OUTPUT_FILE_PNG = 'generation.png'
                          
DEBUG = True

def load_initial_state(filename):
    '''
    @requires: filename ϵ string 
    @modifies: None
    @effects: None
    @raises: None
    @returns: return Downloading the initial configuration from a CSV fileDownloading the initial configuration from a CSV file
    '''
    global WIDTH, HEIGHT
    HEIGHT = 0
    with open(filename, mode='r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            WIDTH = max(WIDTH, len(row))
            HEIGHT = HEIGHT+1
        
    # Создаем начальное состояние поля
    field = [[0 for x in range(WIDTH)] for y in range(HEIGHT)] 
    # Загружаем начальные значения
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for i, row in enumerate(reader):
            for j, cell in enumerate(row):
                field[i][j] = int(cell)           
    return field

def calculate_next_generation(field):
    '''
    @requires: field ϵ [] 
    @modifies: None
    @effects: None
    @raises: None
    @returns: return Calculating the next generation according to the rules of the game of Life.
    '''
    new_field = [[0 for x in range(WIDTH)] for y in range(HEIGHT)]
    
    for i in range(HEIGHT):
        for j in range(WIDTH):
            # Подсчет соседей
            neighbors = sum(
                [field[i-1][j-1] if i > 0 and j > 0 else 0,
                field[i-1][j] if i > 0 else 0,
                field[i-1][j+1] if i > 0 and j < WIDTH-1 else 0,
                field[i][j-1] if j > 0 else 0,
                field[i][j+1] if j < WIDTH-1 else 0,
                field[i+1][j-1] if i < HEIGHT-1 and j > 0 else 0,
                field[i+1][j] if i < HEIGHT-1 else 0,
                field[i+1][j+1] if i < HEIGHT-1 and j < WIDTH-1 else 0]
            )
            
            if field[i][j]:
                # Живая клетка: 3 соседа - выживает, 2 соседа - умирает, 1 сосед - умирает
                if neighbors == 2 or neighbors == 3:
                    new_field[i][j] = 1
                else:
                    new_field[i][j] = 0
            else:
                # Мертвая клетка: 3 соседа - оживает, остальные - умирает
                if neighbors == 3:
                    new_field[i][j] = 1
                else:
                    new_field[i][j] = 0
                    
    return new_field

def draw_field(field, filename):
    '''
    @requires: field  ϵ [], filename ϵ string 
    @modifies: None
    @effects: None
    @raises: None
    @returns: return Drawing a field in PNG format.
    '''
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BASE_COLOR)
    draw = ImageDraw.Draw(img)
    
    for i in range(HEIGHT):
        for j in range(WIDTH):
            if field[i][j]:
                # Определяем оттенок в зависимости от "возраста"
                age = i + j
                r = age % 255
                g = age % 255
                b = age % 255
                draw.rectangle((j, i, j+1, i+1), fill=(r, g, b))
    
    img.save(filename)

def main():
    '''
    @requires: None 
    @modifies: None
    @effects: None
    @raises: None
    @returns: None
    '''
    initial_field = load_initial_state(INPUT_FILE )
    
    for step in range(GENERATIONS):
        print(f"Шаг {step+1}")
        
        # Вычисление следующего поколения
        next_field = calculate_next_generation(initial_field)
        
        # Сохранение состояния поля
        with open(OUTPUT_FILE_CSV, 'w') as file:
            writer = csv.writer(file)
            for row in next_field:
                writer.writerow(row)
                
        # Рисование текущего состояния
        draw_field(next_field, OUTPUT_FILE_PNG)
        
        initial_field = next_field

if __name__ == "__main__":
    main()