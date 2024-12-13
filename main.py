import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

class CrossDockApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Cross-Dock Management")
        self.geometry("1745x800")

        self.unload_file = "unload_queue.txt"
        self.load_file = "load_queue.txt"
        self.warehouse_file = "warehouse.txt"
        self.unload_times_file = "unload_times.txt"
        self.load_times_file = "load_times.txt"
        self.history_file = "history_of_actions.txt"

        self.unload_queue = []
        self.load_queue = []
        self.warehouse = {}


        self.current_unload = None
        self.current_load = None

        self.unload_start_time = None
        self.unload_end_time = None
        self.load_start_time = None
        self.load_end_time = None

        self.unload_times = []
        self.load_times = []

        self.gantt_window = tk.Toplevel(self)
        self.gantt_window.title("Диаграмма Ганта")
        self.gantt_window.geometry("1200x600")

        self.gantt_ax = None
        self.update_gantt_chart()

        self.load_data()
        self.create_widgets()
        self.update_operation_status()

        self.simulate_cross_docking()

    def create_widgets(self):
        tk.Label(self, text="Очередь на разгрузку", font=("Arial", 14)).grid(row=0, column=0, padx=10, pady=10)
        tk.Label(self, text="Очередь на загрузку", font=("Arial", 14)).grid(row=0, column=1, padx=10, pady=10)
        tk.Label(self, text="Товары на складе", font=("Arial", 14)).grid(row=0, column=2, padx=10, pady=10)

        self.unload_table = self.create_table(("№", "Гос. Номер", "Время", "Товар", "Количество"))
        self.unload_table.grid(row=1, column=0, padx=10, pady=10)
        self.load_table = self.create_table(("№", "Гос. Номер", "Время", "Товар", "Количество"))
        self.load_table.grid(row=1, column=1, padx=10, pady=10)

        self.warehouse_table = self.create_table(("№", "Время разгрузки", "Товар", "Количество"))
        self.warehouse_table.grid(row=1, column=2, padx=10, pady=10)

        self.create_input_fields()

        self.unload_status = tk.Label(self, text="На разгрузке: -", font=("Arial", 12))
        self.unload_status.grid(row=3, column=0, pady=10)

        self.load_status = tk.Label(self, text="На загрузке: -", font=("Arial", 12))
        self.load_status.grid(row=3, column=1, pady=10)

        self.update_table(self.unload_table, self.unload_queue)
        self.update_table(self.load_table, self.load_queue)
        self.update_warehouse_table()

        fig, self.gantt_ax = plt.subplots(figsize=(12, 8))
        self.gantt_canvas = FigureCanvasTkAgg(fig, master=self.gantt_window)
        self.gantt_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_input_fields(self):
        input_frame = tk.Frame(self)
        input_frame.grid(row=2, column=0, columnspan=3, pady=10)

        registration_numbers = [
            "В009НУ 142 (разгрузка)",
            "В314НС 142 (разгрузка)",
            "У945НУ 142 (разгрузка)",
            "Т959КС 142 (загрузка)",
            "А130НХ 142 (загрузка)",
            "М503НО 142 (загрузка)"
        ]
        product_name = [
            "Товар 1",
            "Товар 2",
            "Товар 3"
        ]

        tk.Label(input_frame, text="Гос. Номер:").grid(row=0, column=0, padx=5)
        self.plate_combobox = ttk.Combobox(input_frame, values=registration_numbers)
        self.plate_combobox.grid(row=0, column=1, padx=5)

        tk.Label(input_frame, text="Наименование товара:").grid(row=0, column=2, padx=5)
        self.item_combobox = ttk.Combobox(input_frame, values=product_name)
        self.item_combobox.grid(row=0, column=3, padx=5)

        tk.Label(input_frame, text="Количество:").grid(row=0, column=4, padx=5)
        self.quantity_entry = tk.Entry(input_frame)
        self.quantity_entry.grid(row=0, column=5, padx=5)

        tk.Button(input_frame, text="Добавить на разгрузку", command=self.add_to_unload).grid(row=1, column=0,
                                                                                              columnspan=2, pady=5)
        tk.Button(input_frame, text="Добавить на загрузку", command=self.add_to_load).grid(row=1, column=2,
                                                                                           columnspan=2, pady=5)
        tk.Button(input_frame, text="Разгрузить", command=self.start_unload).grid(row=1, column=4, pady=5)
        tk.Button(input_frame, text="Загрузить", command=self.start_load).grid(row=1, column=5, pady=5)

    """Работа с файлами"""
    def load_data(self):
        self.unload_queue = self.read_from_file(self.unload_file)
        self.load_queue = self.read_from_file(self.load_file)
        warehouse_data = self.read_from_file(self.warehouse_file, is_warehouse=True)
        self.unload_times = self.read_times_from_file(self.unload_times_file)
        self.load_times = self.read_times_from_file(self.load_times_file)

        for time, item, quantity in warehouse_data:
            if item in self.warehouse:
                prev_time, prev_quantity = self.warehouse[item]
                self.warehouse[item] = (prev_time, prev_quantity + quantity)
            else:
                self.warehouse[item] = (time, quantity)

    def read_from_file(self, filename, is_warehouse=False):
        data = []
        try:
            with open(filename, "r", encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) == 4 and not is_warehouse:
                        data.append((parts[0], parts[1], parts[2], int(parts[3])))
                    elif len(parts) == 3 and is_warehouse:
                        data.append((parts[0], parts[1], int(parts[2])))
        except FileNotFoundError:
            pass
        return data

    def read_times_from_file(self, filename):
        times = []
        try:
            with open(filename, "r", encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) == 2:
                        times.append((parts[0], parts[1]))
        except FileNotFoundError:
            pass
        return times

    def save_data(self):
        self.write_to_file(self.unload_file, self.unload_queue)
        self.write_to_file(self.load_file, self.load_queue)
        warehouse_data = [
            (time, item, quantity) for item, (time, quantity) in self.warehouse.items()
        ]
        self.write_to_file(self.warehouse_file, warehouse_data)

        self.save_times_to_file(self.unload_times_file, self.unload_times)
        self.save_times_to_file(self.load_times_file, self.load_times)

    def write_to_file(self, filename, data):
        with open(filename, "w", encoding='utf-8') as f:
            for record in data:
                f.write(";".join(map(str, record)) + "\n")

    def save_times_to_file(self, filename, times):
        with open(filename, "w", encoding='utf-8') as f:
            for record in times:
                f.write(";".join(map(str, record)) + "\n")

    def read_history_from_file(self):
        data = []
        with open('history_of_actions.txt', 'r', encoding='utf-8') as file:
            for line in file:
                parts = line.strip().split(';')
                data.append(tuple(parts))
        return data

    """Диаграмма Ганта"""
    def update_gantt_chart(self):
        if not hasattr(self, 'gantt_canvas'):
            return
        data = self.read_history_from_file()

        columns = ["Operation", "Vehicle", "Time", "Item", "Quantity", "Start", "End"]
        df = pd.DataFrame(data, columns=columns)

        df["Start"] = pd.to_datetime(df["Start"], format="%H:%M:%S")
        df["End"] = pd.to_datetime(df["End"], format="%H:%M:%S")

        df["Duration"] = (df["End"] - df["Start"]).dt.total_seconds()

        earliest_start = df["Start"].min()
        df["Relative Start"] = (df["Start"] - earliest_start).dt.total_seconds()

        product_colors = {
            "Товар 1": "green",
            "Товар 2": "blue",
            "Товар 3": "red",
        }

        df["Color"] = df["Item"].map(product_colors).fillna("gray")  # Default to gray if product is not defined

        if self.gantt_ax is None:
            self.gantt_ax = plt.subplots(figsize=(12, 8))

        self.gantt_ax.clear()
        operations = df["Operation"].unique()
        for _, operation in enumerate(operations):
            operation_data = df[df["Operation"] == operation]
            for _, row in operation_data.iterrows():
                self.gantt_ax.barh(
                    operation,
                    row["Duration"],
                    left=row["Relative Start"],
                    color=row["Color"],
                    edgecolor="black",
                )

        plt.xlabel("Время (HH:MM:SS)")
        plt.ylabel("Операция")
        plt.title("Диаграмма Ганта")

        time_labels = pd.to_timedelta(self.gantt_ax.get_xticks(), unit='s') + earliest_start
        filtered_labels = [label.time() if pd.notna(label) else None for label in time_labels]

        self.gantt_ax.set_xticks(self.gantt_ax.get_xticks())
        self.gantt_ax.set_xticklabels([str(label) if label is not None else '' for label in filtered_labels])

        handles = [plt.Line2D([0], [0], color=color, lw=4) for color in product_colors.values()]
        labels = list(product_colors.keys())
        self.gantt_ax.legend(handles, labels, title="Товары")

        self.gantt_canvas.draw()

    def get_car_data(self):
        plate = self.plate_combobox.get()
        item = self.item_combobox.get()
        quantity = self.quantity_entry.get()

        if not plate or not item or not quantity:
            return None

        try:
            quantity = int(quantity)
        except ValueError:
            return None

        time_arrived = datetime.now().strftime("%H:%M:%S")
        self.clear_input_fields()
        return (plate, time_arrived, item, quantity)

    def add_to_unload(self):
        car_data = self.get_car_data()
        if car_data:
            self.unload_queue.append(car_data)
            self.update_table(self.unload_table, self.unload_queue)
            self.clear_input_fields()
            self.save_data()

    def add_to_load(self):
        car_data = self.get_car_data()
        if car_data:
            self.load_queue.append(car_data)
            self.update_table(self.load_table, self.load_queue)
            self.clear_input_fields()
            self.save_data()

    def create_table(self, columns):
        table = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            table.heading(col, text=col)
            table.column(col, width=93)
        return table

    def update_table(self, table, data):
        table.delete(*table.get_children())
        for i, entry in enumerate(data, start=1):
            table.insert("", "end", values=(i, *entry))

    """Работа со складом"""
    def update_warehouse_table(self):
        self.warehouse_table.delete(*self.warehouse_table.get_children())
        for i, (item, (time, quantity)) in enumerate(self.warehouse.items(), start=1):
            self.warehouse_table.insert("", "end", values=(i, time, item, quantity))

    """Оценка приоритетов с учетом взвешенных факторов"""
    def calculate_priority(self, task, task_type):
        _, time_arrived, item, _ = task
        waiting_time = (datetime.now() - datetime.strptime(time_arrived, "%H:%M:%S")).seconds

        weights = {
            "waiting_time": 2.0,  # Срочность
            "dependency": 3.0,   # Зависимость
            "availability": 1.0,  # Доступность
        }

        dependency_score, availability_score = 0, 0
        waiting_score = waiting_time * weights["waiting_time"]

        if task_type == "unload":
            dependency_score = self.is_item_needed_for_load(item) * weights["dependency"]
        elif task_type == "load":
            availability_score = self.is_item_available_in_warehouse(item) * weights["availability"]

        priority = dependency_score + waiting_score + availability_score
        return priority


    # Проверяет, нужен ли товар для задач на загрузку, и возвращает его индекс в очереди загрузки.
    def is_item_needed_for_load(self, item):
        for index, load_item in enumerate(self.load_queue):
            if load_item[2] == item:
                return len(self.load_queue) - index
        return 0

    # Возвращает True, если товар есть на складе в достаточном количестве.
    def is_item_available_in_warehouse(self, item):
        return item in self.warehouse and self.warehouse[item][1] > 0

    """Разгрузка с улучшенным приоритетом"""
    def start_unload(self):
        if self.current_unload is None and self.unload_queue:
            self.unload_start_time = datetime.now().strftime("%H:%M:%S")
            
            self.unload_queue.sort(key=lambda x: self.calculate_priority(x, "unload"), reverse=True)
            
            self.current_unload = self.unload_queue.pop(0)
            self.unload_end_time = (datetime.strptime(self.unload_start_time, "%H:%M:%S") + self.calculate_unload_time()).strftime("%H:%M:%S")
            self.update_table(self.unload_table, self.unload_queue)
            self.unload_status.config(text=f"На разгрузке: {self.current_unload[0]}; {self.current_unload[2]}; {self.current_unload[3]}")

    def calculate_unload_time(self):
        for i in range(0, len(self.unload_times)):
            if self.current_unload[2] == self.unload_times[i][0]:
                time = int(self.current_unload[3]) * int(self.unload_times[i][1])
                return timedelta(seconds=time)
        return timedelta(seconds=0)

    """Загрузка с улучшенным приоритетом"""
    def start_load(self):
        if self.current_load is None and self.load_queue:
            self.load_start_time = datetime.now().strftime("%H:%M:%S")
            
            self.load_queue.sort(key=lambda x: self.calculate_priority(x, "load"), reverse=True)
            
            self.current_load = self.load_queue.pop(0)
            plate, time_arrived, item, quantity = self.current_load

            if item in self.warehouse:
                if self.warehouse[item][1] >= quantity:
                    self.load_end_time = (datetime.strptime(self.load_start_time, "%H:%M:%S") + self.calculate_load_time()).strftime("%H:%M:%S")
                    self.update_table(self.load_table, self.load_queue)
                    self.load_status.config(text=f"На загрузке: {plate}; {item}; {quantity}")
                else:
                    new_quantity = self.warehouse[item][1]
                    self.current_load = (plate, time_arrived, item, new_quantity)
                    self.load_end_time = (datetime.strptime(self.load_start_time, "%H:%M:%S") + self.calculate_load_time()).strftime("%H:%M:%S")
                    print(self.load_start_time, self.calculate_load_time())
                    self.update_table(self.load_table, self.load_queue)
                    self.load_status.config(text=f"На загрузке: частично {plate}; {item}; {new_quantity}")

                    self.load_queue.append((plate, time_arrived, item, quantity - new_quantity))
                    self.update_table(self.load_table, self.load_queue)
            else:
                self.load_queue.insert(0, self.current_load)
                self.current_load = None
                self.load_status.config(text="На загрузке: ожидание товара")

    def calculate_load_time(self):
        for i in range(0, len(self.load_times)):
            if self.current_load[2] == self.load_times[i][0]:
                time = int(self.current_load[3]) * int(self.load_times[i][1])
                return timedelta(seconds=time)
        return timedelta(seconds=0)

    """Обновление всех данных программы, логирование процессов"""
    def update_operation_status(self):
        now = datetime.now().strftime("%H:%M:%S")

        if self.current_unload and now >= self.unload_end_time:
            _, _, item, quantity = self.current_unload
            if item in self.warehouse:
                current_quantity = self.warehouse[item][1]
                self.warehouse[item] = (now, current_quantity + quantity)
            else:
                self.warehouse[item] = (now, quantity)

            self.update_warehouse_table()
            self.log_operation("Завершена разгрузка", self.current_unload, self.unload_start_time, 
                               self.unload_end_time)
            self.current_unload = None
            self.unload_status.config(text="На разгрузке: -")
            self.save_data()

            self.after(1000, self.start_unload)

        if self.current_load and self.load_end_time is not None and now >= self.load_end_time:
            _, _, item, quantity = self.current_load
            if item in self.warehouse and self.warehouse[item][1] >= quantity:
                self.warehouse[item] = (self.warehouse[item][0], self.warehouse[item][1] - quantity)
                if self.warehouse[item][1] == 0:
                    del self.warehouse[item]
            self.update_warehouse_table()
            self.update_table(self.load_table, self.load_queue)
            self.log_operation("Завершена загрузка", self.current_load, self.load_start_time, 
                               self.load_end_time)
            self.current_load = None
            self.load_status.config(text="На загрузке: -")
            self.save_data()

            self.after(1000, self.start_load)

        self.update_gantt_chart()
        self.after(1000, self.update_operation_status)

    def log_operation(self, action, data, start_time, end_time):
        with open(self.history_file, "a", encoding='utf-8') as f:
            f.write(f"{action};{';'.join(map(str, data))};{start_time};{end_time}\n")

    def clear_input_fields(self):
        self.plate_combobox.set("")
        self.item_combobox.set("")
        self.quantity_entry.delete(0, tk.END)

    """Запуск симуляции кросс-докинга"""
    def simulate_cross_docking(self):
        if self.current_unload is None and self.unload_queue:
            self.after(1000, self.start_unload)
        if self.current_load is None and self.load_queue:
            self.after(1000, self.start_load)

        self.after(1000, self.simulate_cross_docking)


if __name__ == "__main__":
    app = CrossDockApp()
    app.mainloop()

