import sys
import csv
import shutil
from pathlib import Path
from PyQt6.QtCore import Qt, QDate, QSettings
from PyQt6.QtWidgets import (QApplication,QWidget,QMainWindow,QDialog,QLabel,
    QLineEdit,QTextEdit,QPushButton,QVBoxLayout,QHBoxLayout,QFormLayout,
    QMessageBox,QComboBox,QTableWidget,QTableWidgetItem,QTabWidget,QFileDialog,
    QDateEdit,QInputDialog,QHeaderView
)
import database

class LoginDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.resize(350, 200)

        self.username = QLineEdit()
        self.password = QLineEdit()

        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Login")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.password)
        layout.addWidget(self.login_button)

        self.login_button.clicked.connect(self.check_login)

    def check_login(self):
        if database.login(self.username.text(), self.password.text()):
            self.accept()

        else:
            QMessageBox.warning(self,"Login failed","Username หรือ Password ไม่ถูกต้อง")


class TaskManager(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SQLite Task Manager PRO")
        self.resize(1100, 750)

        self.settings = QSettings("TaskManagerPRO","TaskManager")

        self.selected_task_id = None
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.create_task_tab()
        self.create_dashboard_tab()
        self.create_category_tab()
        self.create_menu_buttons()
        self.load_categories()
        self.load_tasks()
        self.refresh_dashboard()
        self.load_theme()
        self.check_due_tasks()

    def create_task_tab(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        form = QFormLayout()
        self.title_input = QLineEdit()
        self.detail_input = QTextEdit()
        self.detail_input.setMaximumHeight(100)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low","Medium","High"])
        self.priority_combo.setCurrentText("Medium")
        self.category_combo = QComboBox()
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate())
        self.due_date.setDisplayFormat("yyyy-MM-dd")

        form.addRow("ชื่องาน:",self.title_input)
        form.addRow("รายละเอียด:",self.detail_input)
        form.addRow("Priority:",self.priority_combo)
        form.addRow("Category:",self.category_combo)
        form.addRow("Due Date:",self.due_date)
        main_layout.addLayout(form)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("เพิ่มงาน")
        self.update_button = QPushButton("แก้ไข")
        self.delete_button = QPushButton("ลบ")
        self.done_button = QPushButton("เสร็จแล้ว")
        self.duplicate_button = QPushButton("Duplicate")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.done_button)
        button_layout.addWidget(self.duplicate_button)
        main_layout.addLayout(button_layout)
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ค้นหาชื่องาน...")
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All",
            "todo",
            "done"
        ])

        self.priority_filter = QComboBox()
        self.priority_filter.addItems([
            "All",
            "High",
            "Medium",
            "Low"
        ])

        self.category_filter = QComboBox()

        filter_layout.addWidget(
            QLabel("Search:")
        )

        filter_layout.addWidget(
            self.search_input
        )

        filter_layout.addWidget(
            QLabel("Status:")
        )

        filter_layout.addWidget(
            self.status_filter
        )

        filter_layout.addWidget(
            QLabel("Priority:")
        )

        filter_layout.addWidget(
            self.priority_filter
        )

        filter_layout.addWidget(
            QLabel("Category:")
        )

        filter_layout.addWidget(
            self.category_filter
        )

        main_layout.addLayout(
            filter_layout
        )

        self.task_table = QTableWidget()

        self.task_table.setColumnCount(8)

        self.task_table.setHorizontalHeaderLabels([
            "ID",
            "Title",
            "Detail",
            "Status",
            "Priority",
            "Category",
            "Due Date",
            "Completed At"
        ])

        self.task_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.task_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.task_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        main_layout.addWidget(
            self.task_table
        )

        self.tabs.addTab(
            page,
            "Tasks"
        )

        # signals

        self.add_button.clicked.connect(
            self.add_task
        )

        self.update_button.clicked.connect(
            self.update_task
        )

        self.delete_button.clicked.connect(
            self.delete_task
        )

        self.done_button.clicked.connect(
            self.mark_done
        )

        self.duplicate_button.clicked.connect(
            self.duplicate_task
        )

        self.task_table.cellClicked.connect(
            self.select_task
        )

        self.search_input.textChanged.connect(
            self.load_tasks
        )

        self.status_filter.currentTextChanged.connect(
            self.load_tasks
        )

        self.priority_filter.currentTextChanged.connect(
            self.load_tasks
        )

        self.category_filter.currentIndexChanged.connect(
            self.load_tasks
        )

    def add_task(self):

        title = self.title_input.text()

        if not title.strip():

            QMessageBox.warning(
                self,
                "Warning",
                "กรุณากรอกชื่องาน"
            )

            return

        category_id = self.category_combo.currentData()

        database.add_task(
            title,
            self.detail_input.toPlainText(),
            self.due_date.date().toString(
                "yyyy-MM-dd"
            ),
            self.priority_combo.currentText(),
            category_id
        )

        self.clear_form()

        self.load_tasks()

        self.refresh_dashboard()

    def select_task(self, row, column):

        task_id = int(
            self.task_table.item(
                row,
                0
            ).text()
        )

        task = database.get_task(
            task_id
        )

        if not task:
            return

        self.selected_task_id = task_id

        self.title_input.setText(
            task["title"]
        )

        self.detail_input.setPlainText(
            task["detail"] or ""
        )

        self.priority_combo.setCurrentText(
            task["priority"]
        )

        category_index = self.category_combo.findData(
            task["category_id"]
        )

        if category_index >= 0:
            self.category_combo.setCurrentIndex(
                category_index
            )

        if task["due_date"]:

            date = QDate.fromString(
                task["due_date"],
                "yyyy-MM-dd"
            )

            if date.isValid():
                self.due_date.setDate(
                    date
                )

    def update_task(self):

        if self.selected_task_id is None:

            QMessageBox.warning(
                self,
                "Warning",
                "กรุณาเลือกงานก่อน"
            )

            return

        database.update_task(
            self.selected_task_id,
            self.title_input.text(),
            self.detail_input.toPlainText(),
            self.due_date.date().toString(
                "yyyy-MM-dd"
            ),
            self.priority_combo.currentText(),
            self.category_combo.currentData()
        )

        self.clear_form()

        self.load_tasks()

        self.refresh_dashboard()

    def delete_task(self):

        if self.selected_task_id is None:

            QMessageBox.warning(
                self,
                "Warning",
                "กรุณาเลือกงาน"
            )

            return

        result = QMessageBox.question(
            self,
            "Delete",
            "ต้องการลบงานนี้หรือไม่?"
        )

        if result == QMessageBox.StandardButton.Yes:

            database.delete_task(
                self.selected_task_id
            )

            self.selected_task_id = None

            self.load_tasks()

            self.refresh_dashboard()

    def mark_done(self):

        if self.selected_task_id is None:

            QMessageBox.warning(
                self,
                "Warning",
                "กรุณาเลือกงาน"
            )

            return

        database.update_status(
            self.selected_task_id,
            "done"
        )

        self.load_tasks()

        self.refresh_dashboard()

    def duplicate_task(self):

        if self.selected_task_id is None:

            QMessageBox.warning(
                self,
                "Warning",
                "กรุณาเลือกงาน"
            )

            return

        database.duplicate_task(
            self.selected_task_id
        )

        self.load_tasks()

        self.refresh_dashboard()

    def load_tasks(self, *args):

        category_id = self.category_filter.currentData()

        tasks = database.list_tasks(
            keyword=self.search_input.text(),
            status=self.status_filter.currentText(),
            priority=self.priority_filter.currentText(),
            category_id=category_id
        )

        self.task_table.setRowCount(
            len(tasks)
        )

        for row, task in enumerate(tasks):

            values = [
                task["id"],
                task["title"],
                task["detail"],
                task["status"],
                task["priority"],
                task["category"] or "-",
                task["due_date"] or "-",
                task["completed_at"] or "-"
            ]

            for col, value in enumerate(values):

                self.task_table.setItem(
                    row,
                    col,
                    QTableWidgetItem(
                        str(value)
                    )
                )


    # =====================================================
    # CLEAR FORM
    # =====================================================

    def clear_form(self):

        self.selected_task_id = None

        self.title_input.clear()

        self.detail_input.clear()

        self.priority_combo.setCurrentText(
            "Medium"
        )


    # =====================================================
    # CATEGORY TAB
    # =====================================================

    def create_category_tab(self):

        page = QWidget()

        layout = QVBoxLayout(page)

        self.category_table = QTableWidget()

        self.category_table.setColumnCount(2)

        self.category_table.setHorizontalHeaderLabels([
            "ID",
            "Category"
        ])

        self.category_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(
            self.category_table
        )

        button_layout = QHBoxLayout()

        add_button = QPushButton(
            "เพิ่มหมวดหมู่"
        )

        edit_button = QPushButton(
            "แก้ไขหมวดหมู่"
        )

        delete_button = QPushButton(
            "ลบหมวดหมู่"
        )

        button_layout.addWidget(
            add_button
        )

        button_layout.addWidget(
            edit_button
        )

        button_layout.addWidget(
            delete_button
        )

        layout.addLayout(
            button_layout
        )

        self.tabs.addTab(
            page,
            "Categories"
        )

        add_button.clicked.connect(
            self.add_category
        )

        edit_button.clicked.connect(
            self.edit_category
        )

        delete_button.clicked.connect(
            self.delete_category
        )


    def load_categories(self):

        categories = database.list_categories()

        self.category_combo.clear()

        self.category_filter.clear()

        self.category_filter.addItem(
            "All",
            None
        )

        for category in categories:

            self.category_combo.addItem(
                category["name"],
                category["id"]
            )

            self.category_filter.addItem(
                category["name"],
                category["id"]
            )

        self.category_table.setRowCount(
            len(categories)
        )

        for row, category in enumerate(categories):

            self.category_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    str(category["id"])
                )
            )

            self.category_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    category["name"]
                )
            )


    def add_category(self):

        name, ok = QInputDialog.getText(
            self,
            "Add Category",
            "ชื่อหมวดหมู่:"
        )

        if ok and name:

            if not database.add_category(name):

                QMessageBox.warning(
                    self,
                    "Warning",
                    "หมวดหมู่นี้มีอยู่แล้ว"
                )

            self.load_categories()


    def edit_category(self):

        row = self.category_table.currentRow()

        if row < 0:
            return

        category_id = int(
            self.category_table.item(
                row,
                0
            ).text()
        )

        old_name = self.category_table.item(
            row,
            1
        ).text()

        name, ok = QInputDialog.getText(
            self,
            "Edit Category",
            "ชื่อใหม่:",
            text=old_name
        )

        if ok and name:

            database.update_category(
                category_id,
                name
            )

            self.load_categories()


    def delete_category(self):

        row = self.category_table.currentRow()

        if row < 0:
            return

        category_id = int(
            self.category_table.item(
                row,
                0
            ).text()
        )

        database.delete_category(
            category_id
        )

        self.load_categories()

        self.load_tasks()

    def create_dashboard_tab(self):

        page = QWidget()

        layout = QVBoxLayout(page)

        self.total_label = QLabel()
        self.done_label = QLabel()
        self.todo_label = QLabel()
        self.overdue_label = QLabel()
        self.near_due_label = QLabel()

        layout.addWidget(
            self.total_label
        )

        layout.addWidget(
            self.done_label
        )

        layout.addWidget(
            self.todo_label
        )

        layout.addWidget(
            self.overdue_label
        )

        layout.addWidget(
            self.near_due_label
        )

        self.category_count_label = QLabel()

        self.priority_count_label = QLabel()

        layout.addWidget(
            self.category_count_label
        )

        layout.addWidget(
            self.priority_count_label
        )

        self.tabs.addTab(
            page,
            "Dashboard"
        )


    def refresh_dashboard(self):

        data = database.dashboard_counts()

        self.total_label.setText(
            f"งานทั้งหมด: {data['total']}"
        )

        self.done_label.setText(
            f"งานที่เสร็จแล้ว: {data['done']}"
        )

        self.todo_label.setText(
            f"งานค้าง: {data['todo']}"
        )

        self.overdue_label.setText(
            f"งานเลยกำหนด: {data['overdue']}"
        )

        self.near_due_label.setText(
            f"งานใกล้ครบกำหนด: {data['near_due']}"
        )

        category_text = "\n".join(
            f"{row[0]} : {row[1]}"
            for row in database.count_by_category()
        )

        self.category_count_label.setText(
            "จำนวนงานตาม Category\n\n"
            + category_text
        )

        priority_text = "\n".join(
            f"{row[0]} : {row[1]}"
            for row in database.count_by_priority()
        )

        self.priority_count_label.setText(
            "จำนวนงานตาม Priority\n\n"
            + priority_text
        )

    def export_csv(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "tasks.csv",
            "CSV Files (*.csv)"
        )

        if not path:
            return

        tasks = database.list_tasks()

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "title",
                "detail",
                "status",
                "priority",
                "category",
                "due_date"
            ])

            for task in tasks:

                writer.writerow([
                    task["title"],
                    task["detail"],
                    task["status"],
                    task["priority"],
                    task["category"] or "",
                    task["due_date"] or ""
                ])

        QMessageBox.information(
            self,
            "Export",
            "Export CSV สำเร็จ"
        )


    def import_csv(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not path:
            return

        try:

            with open(
                path,
                "r",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                required = {
                    "title",
                    "detail",
                    "priority",
                    "due_date"
                }

                if not required.issubset(
                    reader.fieldnames or []
                ):

                    QMessageBox.warning(
                        self,
                        "Invalid CSV",
                        "รูปแบบ CSV ไม่ถูกต้อง"
                    )

                    return

                for row in reader:

                    title = row[
                        "title"
                    ].strip()

                    if not title:
                        continue

                    priority = row[
                        "priority"
                    ]

                    if priority not in [
                        "Low",
                        "Medium",
                        "High"
                    ]:
                        priority = "Medium"

                    category_id = None

                    category_name = row.get(
                        "category",
                        ""
                    ).strip()

                    if category_name:

                        database.add_category(
                            category_name
                        )

                        for category in database.list_categories():

                            if category["name"] == category_name:

                                category_id = category[
                                    "id"
                                ]

                                break

                    database.add_task(
                        title,
                        row["detail"],
                        row["due_date"],
                        priority,
                        category_id
                    )

            self.load_categories()
            self.load_tasks()
            self.refresh_dashboard()

            QMessageBox.information(
                self,
                "Import",
                "Import CSV สำเร็จ"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                str(error)
            )

    def backup_database(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Database",
            "tasks_backup.db",
            "SQLite Database (*.db)"
        )

        if not path:
            return

        shutil.copy2(
            database.DB_PATH,
            path
        )

        QMessageBox.information(
            self,
            "Backup",
            "Backup สำเร็จ"
        )


    def restore_database(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Database",
            "",
            "SQLite Database (*.db)"
        )

        if not path:
            return

        result = QMessageBox.question(
            self,
            "Restore",
            "ข้อมูลปัจจุบันจะถูกแทนที่ ต้องการดำเนินการต่อหรือไม่?"
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        shutil.copy2(
            path,
            database.DB_PATH
        )

        database.initialize()

        self.load_categories()
        self.load_tasks()
        self.refresh_dashboard()

        QMessageBox.information(
            self,
            "Restore",
            "Restore สำเร็จ"
        )

    def toggle_theme(self):

        current = self.settings.value(
            "theme",
            "light"
        )

        if current == "light":

            self.settings.setValue(
                "theme",
                "dark"
            )

        else:

            self.settings.setValue(
                "theme",
                "light"
            )

        self.load_theme()


    def load_theme(self):

        theme = self.settings.value(
            "theme",
            "light"
        )

        if theme == "dark":

            self.setStyleSheet("""
                QWidget {
                    background-color: #202124;
                    color: white;
                    font-size: 14px;
                }

                QLineEdit,
                QTextEdit,
                QComboBox,
                QDateEdit,
                QTableWidget {
                    background-color: #303134;
                    color: white;
                }

                QPushButton {
                    background-color: #3c4043;
                    color: white;
                    padding: 6px;
                }

                QPushButton:hover {
                    background-color: #5f6368;
                }
            """)

        else:

            self.setStyleSheet("")

    def check_due_tasks(self):

        tasks = database.get_due_alerts()

        if not tasks:
            return

        message = ""

        for task in tasks:

            message += (
                f"{task['title']} "
                f"- {task['due_date']}\n"
            )

        QMessageBox.warning(
            self,
            "แจ้งเตือนงาน",
            "งานใกล้ครบกำหนดหรือเลยกำหนด:\n\n"
            + message
        )

    def create_menu_buttons(self):

        toolbar = self.addToolBar("Tools")
        export_action = toolbar.addAction("Export CSV")
        import_action = toolbar.addAction("Import CSV")
        backup_action = toolbar.addAction("Backup")
        restore_action = toolbar.addAction("Restore")
        theme_action = toolbar.addAction("Light / Dark")
        export_action.triggered.connect(self.export_csv)
        import_action.triggered.connect(self.import_csv)
        backup_action.triggered.connect(self.backup_database)
        restore_action.triggered.connect(self.restore_database)
        theme_action.triggered.connect(self.toggle_theme)

database.initialize()
app = QApplication(sys.argv)
login = LoginDialog()
if login.exec() == QDialog.DialogCode.Accepted:
    window = TaskManager()
    window.show()
    sys.exit(app.exec())