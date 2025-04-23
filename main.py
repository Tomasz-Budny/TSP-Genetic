import tkinter as tk
import random
import numpy as np
import math
from PIL import Image, ImageTk
import os

# --- Parametry algorytmu ---
POPULATION_SIZE = 100
MUTATION_RATE = 0.01
GENERATIONS = 300

# --- GUI ustawienia ---
WINDOW_SIZE = 612
CITY_RADIUS = 5
CITY_COLOR = "#FF5722"         
INDEX_LABEL_OFFSET = 20             # Wysokość indeksu miasta nad kropką
INDEX_LABEL_OFFSET = 20             # Przesunięcie indeksów miast do góry
LABEL_BG_COLOR = "white"            # Tło prostokątów dla indeksów
LABEL_TEXT_COLOR = "black"          # Kolor tekstu indeksu
LABEL_PADDING_X = 3                 # Padding w poziomie w ramce
LABEL_PADDING_Y = 1                 # Padding w pionie w ramce
ARROW_INDEX_LABEL_OFFSET = -10

background_image = None
background_tk = None
city_coords = []
start_city_index = None

# --- Obliczanie długości trasy ---
def route_length(route, cities):
    dist = 0
    for i in range(len(route)):
        x1, y1 = cities[route[i % len(cities)]]
        x2, y2 = cities[route[(i + 1) % len(cities)]]
        dist += math.hypot(x2 - x1, y2 - y1)
    return dist

# --- Tworzenie populacji ---
def create_population(n, start_idx=None):
    pool = list(range(n))
    if start_idx is not None:
        pool.remove(start_idx)
        return [[start_idx] + random.sample(pool, n - 1) for _ in range(POPULATION_SIZE)]
    else:
        return [random.sample(range(n), n) for _ in range(POPULATION_SIZE)]

# --- Selekcja ---
def select(population, cities):
    ranked = sorted(population, key=lambda r: route_length(r, cities))
    return ranked[:POPULATION_SIZE // 2]

# --- Krzyżowanie ---
def crossover(p1, p2):
    fixed_start = p1[0]
    p1_body = p1[1:]
    p2_body = [c for c in p2 if c != fixed_start]

    start, end = sorted(random.sample(range(len(p1_body)), 2))
    child_p1 = p1_body[start:end]
    child_p2 = [c for c in p2_body if c not in child_p1]
    return [fixed_start] + child_p1 + child_p2

def mutate(route):
    if random.random() < MUTATION_RATE:
        i, j = random.sample(range(1, len(route)), 2)
        route[i], route[j] = route[j], route[i]
    return route

def evolve(cities, start_idx=None):
    if len(cities) < 3:
        return [], 0

    population = create_population(len(cities), start_idx)
    best_route = None
    best_distance = float('inf')

    for _ in range(GENERATIONS):
        selected = select(population, cities)
        next_gen = []

        while len(next_gen) < POPULATION_SIZE:
            p1, p2 = random.sample(selected, 2)
            child = crossover(p1, p2)
            next_gen.append(mutate(child))

        population = next_gen
        current_best = min(population, key=lambda r: route_length(r, cities))
        current_distance = route_length(current_best, cities)

        if current_distance < best_distance:
            best_distance = current_distance
            best_route = current_best

    return best_route, best_distance

def index_to_letters(index):
    letters = ""
    while True:
        index, remainder = divmod(index, 26)
        letters = chr(65 + remainder) + letters
        if index == 0:
            break
        index -= 1  
    return letters

def draw_cities():
    canvas.delete("all")

    if background_tk:
        canvas.create_image(0, 0, anchor=tk.NW, image=background_tk)

    for i, (x, y) in enumerate(city_coords):
        color = "green" if i == start_city_index else CITY_COLOR
        canvas.create_oval(x - CITY_RADIUS, y - CITY_RADIUS, x + CITY_RADIUS, y + CITY_RADIUS, fill=color, outline="")

    for i, (x, y) in enumerate(city_coords):
        label_y = y - INDEX_LABEL_OFFSET
        label = index_to_letters(i)
        text_id = canvas.create_text(x, label_y, text=label, font=("Arial", 10, "bold"), fill=LABEL_TEXT_COLOR)
        bbox = canvas.bbox(text_id)
        if bbox:
            x1, y1, x2, y2 = bbox
            x1 -= LABEL_PADDING_X
            x2 += LABEL_PADDING_X
            y1 -= LABEL_PADDING_Y
            y2 += LABEL_PADDING_Y
            canvas.create_rectangle(x1, y1, x2, y2, fill=LABEL_BG_COLOR, outline="black")
            canvas.tag_raise(text_id)

def draw_path(path):
    for i in range(len(path)):
        idx = i % len(path)
        next_idx = (i + 1) % len(path)
        x1, y1 = city_coords[path[idx]]
        x2, y2 = city_coords[path[next_idx]]

        canvas.create_line(x1, y1, x2, y2, fill="black", width=3, arrow=tk.LAST)

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2 + ARROW_INDEX_LABEL_OFFSET

        step_label = str(round(i))
        text_id = canvas.create_text(mid_x, mid_y, text=step_label, font=("Arial", 9, "bold"), fill=LABEL_TEXT_COLOR)
        bbox = canvas.bbox(text_id)
        if bbox:
            x1b, y1b, x2b, y2b = bbox
            x1b -= LABEL_PADDING_X
            x2b += LABEL_PADDING_X
            y1b -= LABEL_PADDING_Y
            y2b += LABEL_PADDING_Y
            canvas.create_oval(x1b, y1b, x2b, y2b, fill=LABEL_BG_COLOR, outline="black")
            canvas.tag_raise(text_id)

def load_background():
    global background_image, background_tk, WINDOW_SIZE
    possible_names = ["background.jpg", "background.jpeg", "background.png", "background.bmp"]
    for name in possible_names:
        if os.path.exists(name):
            background_image = Image.open(name)
            width, height = background_image.size
            WINDOW_SIZE = (width, height)
            background_image = background_image.resize((width, height))
            background_tk = ImageTk.PhotoImage(background_image)
            return
    WINDOW_SIZE = (800, 800)

def on_left_click(event):
    global city_coords, start_city_index
    click_x, click_y = event.x, event.y

    for i, (x, y) in enumerate(city_coords):
        if abs(x - click_x) < 10 and abs(y - click_y) < 10:
            city_coords.pop(i)
            if i == start_city_index:
                reset_start()
            elif start_city_index is not None and i < start_city_index:
                set_start(start_city_index - 1)
            draw_cities()
            return

    city_coords.append((click_x, click_y))
    if len(city_coords) == 1:
        set_start(0)
    draw_cities()

def on_right_click(event):
    click_x, click_y = event.x, event.y
    for i, (x, y) in enumerate(city_coords):
        if abs(x - click_x) < 10 and abs(y - click_y) < 10:
            set_start(i)
            return

def set_start(i):
    global start_city_index
    start_city_index = i
    draw_cities()

def reset_start():
    global start_city_index
    start_city_index = None

def run_algorithm():
    path, dist = evolve(city_coords, start_city_index)
    draw_cities()
    if path:
        draw_path(path)
        city_order = " → ".join(index_to_letters(i) for i in path)
        distance_label.config(text=f"Długość trasy: {dist:.2f}")
        path_label.config(text=f"Kolejność: {city_order}")
    else:
        distance_label.config(text="Za mało miast")
        path_label.config(text="")

def clear_path():
    draw_cities() 
    distance_label.config(text="")
    path_label.config(text="")

def clear_all():
    global city_coords, start_city_index
    city_coords = []
    start_city_index = None
    canvas.delete("all")
    distance_label.config(text="")
    path_label.config(text="")
    draw_cities()

# --- GUI setup ---
root = tk.Tk()
root.title("🧭 TSP Genetic")
root.config(bg="white") 

load_background()

canvas = tk.Canvas(root, width=WINDOW_SIZE[0], height=WINDOW_SIZE[1])
canvas.pack()

canvas.bind("<Button-1>", on_left_click)
canvas.bind("<Button-3>", on_right_click)

button = tk.Button(
    root,
    text="✈️ Start Algorytmu Genetycznego",
    font=("Segoe UI Emoji", 11, "bold"),
    bg="#4CAF50", 
    fg="white",     
    relief="raised", 
    bd=5,           
    command=run_algorithm
)
button.pack(pady=10)

clear_button = tk.Button(
    root,
    text="📍 Wyczyść trasę",
    font=("Segoe UI Emoji", 9, "bold"),
    bg="#ff6875", 
    fg="white",     
    relief="raised",
    bd=5,         
    command=clear_path
)
clear_button.pack(pady=5)

clear_all_button = tk.Button(
    root,
    text="❌ Wyczyść Wszystko",
    font=("Segoe UI Emoji", 9, "bold"),
    bg="#ff6875",
    fg="white", 
    relief="raised",
    bd=5,
    command=clear_all
)
clear_all_button.pack(pady=5)

distance_label = tk.Label(root, text="-", bg="white", font=("Segoe UI Emoji", 12, "bold")) 
distance_label.pack()

path_label = tk.Label(root, text="-", wraplength=580, justify="left", bg="white", font=("Segoe UI Emoji", 12, "bold"))
path_label.pack(pady=10)

load_background()
draw_cities()
root.mainloop()
