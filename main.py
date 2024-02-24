import sqlite3
import sys
from PyQt6.QtWidgets import (
    QWidget, QApplication, QListWidgetItem, QMessageBox,
    QPushButton, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.uic import loadUi

class Window(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('main.ui', self)
        self.calendarWidget.selectionChanged.connect(self.calendarDateChanged)
        self.calendarDateChanged()
        self.saveButton.clicked.connect(self.saveChanges)
        self.addButton.clicked.connect(self.addNewTask)
        self.editButton.clicked.connect(self.editTask)
        self.deleteButton.clicked.connect(self.deleteTask)
        self.searchButton.clicked.connect(self.searchTask)
        self.showCompletedButton.clicked.connect(lambda: self.updateTaskListFilter(True))
        self.showUncompletedButton.clicked.connect(lambda: self.updateTaskListFilter(False))


    def calendarDateChanged(self):
        dateSelected = self.calendarWidget.selectedDate().toPyDate()
        self.updateTaskList(dateSelected)

    def saveChanges(self):
        db = sqlite3.connect('data.db')
        cursor = db.cursor()
        date = self.calendarWidget.selectedDate().toPyDate()

        try:
            for i in range(self.taskslistWidget.count()):
                item = self.taskslistWidget.item(i)
                task = item.text()
                completed = 'Да' if item.checkState() == Qt.CheckState.Checked else 'Нет'
                query = "UPDATE tasks SET completed = ? WHERE task = ? AND date = ?"
                cursor.execute(query, (completed, task, date))
            db.commit()
            QMessageBox.information(self, "Success", "Changes saved successfully.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
        finally:
            db.close()

    def addNewTask(self):
        newTask = self.taskLineEdit.text()
        if newTask:
            date = self.calendarWidget.selectedDate().toPyDate()
            db = sqlite3.connect('data.db')
            cursor = db.cursor()
            query = "INSERT INTO tasks (task, completed, date) VALUES (?, 'Нет', ?)"
            cursor.execute(query, (newTask, date))
            db.commit()
            db.close()
            self.updateTaskList(date)
            self.taskLineEdit.clear()

    def editTask(self):
        currentItem = self.taskslistWidget.currentItem()
        if currentItem:
            oldText = currentItem.text()
            newText, ok = QInputDialog.getText(self, 'Редактирование задачи', 'Введите новый текст задачи:', text=oldText)
            if ok and newText and newText != oldText:
                currentItem.setText(newText)
                self.updateTaskInDatabase(oldText, newText)

    def updateTaskInDatabase(self, oldText, newText):
        date = self.calendarWidget.selectedDate().toPyDate()
        db = sqlite3.connect('data.db')
        cursor = db.cursor()
        try:
            query = "UPDATE tasks SET task = ? WHERE task = ? AND date = ?"
            cursor.execute(query, (newText, oldText, date))
            db.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
        finally:
            db.close()

    def deleteTask(self):
        currentRow = self.taskslistWidget.currentRow()
        if currentRow != -1:
            currentItem = self.taskslistWidget.takeItem(currentRow)
            task = currentItem.text()
            date = self.calendarWidget.selectedDate().toPyDate()
            db = sqlite3.connect('data.db')
            cursor = db.cursor()
            try:
                query = "DELETE FROM tasks WHERE task = ? AND date = ?"
                cursor.execute(query, (task, date))
                db.commit()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")
            finally:
                db.close()

    def searchTask(self):
        text, ok = QInputDialog.getText(self, 'Поиск задачи', 'Введите название задачи:')
        if ok and text:
            self.performSearch(text)

    def performSearch(self, search_text):
        db = sqlite3.connect('data.db')
        cursor = db.cursor()
        query = "SELECT task, completed, date FROM tasks WHERE task LIKE ?"
        search_term = f"%{search_text}%"
        cursor.execute(query, (search_term,))
        results = cursor.fetchall()
        db.close()

        if results:
            message = "\n".join(
                f"{task};{'выполненная' if completed == 'Да' else 'не выполненная'};{date}" for task, completed, date in
                results)
            QMessageBox.information(self, "Результаты поиска", message)
        else:
            QMessageBox.information(self, "Результаты поиска", "Задачи не найдены.")

    def updateTaskListFilter(self, show_completed):
        if self.sender().isChecked():
            dateSelected = self.calendarWidget.selectedDate().toPyDate()
            completed_status = 'Да' if show_completed else 'Нет'
            self.updateTaskList(dateSelected, completed_status)
        else:
            self.showAllTasks()

    def updateTaskList(self, date, completed_status=None):
        self.taskslistWidget.clear()
        db = sqlite3.connect('data.db')
        cursor = db.cursor()

        query = "SELECT task, completed FROM tasks WHERE date = ?"
        params = [date]

        if completed_status is not None:
            query += " AND completed = ?"
            params.append(completed_status)

        results = cursor.execute(query, params).fetchall()
        db.close()

        for result in results:
            item = QListWidgetItem(str(result[0]))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            check_state = Qt.CheckState.Checked if result[1] == 'Да' else Qt.CheckState.Unchecked
            item.setCheckState(check_state)
            self.taskslistWidget.addItem(item)

    def showAllTasks(self):
        self.showCompletedButton.setChecked(False)
        self.showUncompletedButton.setChecked(False)
        dateSelected = self.calendarWidget.selectedDate().toPyDate()
        self.updateTaskList(dateSelected)

    def updateTaskList(self, date, completed_status=None):
        self.taskslistWidget.clear()
        db = sqlite3.connect('data.db')
        cursor = db.cursor()

        query = "SELECT task, completed FROM tasks WHERE date = ?"
        params = [date]

        if completed_status is not None:
            query += " AND completed = ?"
            params.append(completed_status)

        results = cursor.execute(query, params).fetchall()
        db.close()

        for result in results:
            item = QListWidgetItem(str(result[0]))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            check_state = Qt.CheckState.Checked if result[1] == 'Да' else Qt.CheckState.Unchecked
            item.setCheckState(check_state)
            self.taskslistWidget.addItem(item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
