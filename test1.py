import tkinter as tk
import sqlite3


class TodoApp:
    def __init__(self, root, db_name="todo.db"):
        self.root = root
        root.title("Simple To-Do App")
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.create_db()
        self.create_widgets()
        self.tasks = []  # Initialize the tasks list

    def create_db(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    completed INTEGER DEFAULT 0  -- 0 = incomplete, 1 = complete
                )
            """
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def create_widgets(self):
        self.task_entry = tk.Entry(self.root, width=30)
        self.task_entry.pack()
        self.add_button = tk.Button(self.root, text="Add Task", command=self.add_task)
        self.add_button.pack()

        self.task_list = tk.Listbox(self.root, width=40)
        self.task_list.pack()

        self.update_task_list()  # Call update_task_list after widgets are created

        self.delete_button = tk.Button(
            self.root, text="Delete Task", command=self.delete_task
        )
        self.delete_button.pack()

    def add_task(self):
        task_description = self.task_entry.get()
        if task_description:
            self.cursor.execute(
                "INSERT INTO tasks (description) VALUES (?)", (task_description,)
            )
            self.conn.commit()
            self.update_task_list()
            self.task_entry.delete(0, tk.END)

    def update_task_list(self):
        try:
            self.cursor.execute("SELECT id, description, completed FROM tasks")
            self.tasks = []
            for row in self.cursor.fetchall():
                self.tasks.append(
                    (row[0], row[1], row[2] == 1)
                )  # Store id, description, and completed status
        except sqlite3.Error as e:
            print(f"Error fetching tasks: {e}")

    def delete_task(self):
        try:
            selected_task_id = self.task_list.curselection()
            if selected_task_id:
                task_id = self.task_list.get(selected_task_id)
                self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                self.conn.commit()
                self.update_task_list()
        except sqlite3.Error as e:
            print(f"Error deleting task: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
