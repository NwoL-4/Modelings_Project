import streamlit as st
import pages.N_body as nBody

st.set_page_config(
    layout='wide',
    initial_sidebar_state='collapsed'
)

# st.markdown("""
#     <style>
#         section[data-testid="stSidebar"][aria-expanded="true"]{
#             display: none;
#         }
#     </style>
#     """, unsafe_allow_html=True)

# Создаем функции страниц
def home_page():
    st.write("Это главная страница. Здесь можно выбрать Модель для моделирования")

def page_one():
    st.title("Страница 1")
    st.write("Содержимое первой страницы.")

def page_two():
    st.title("Страница 2")
    st.write("Содержимое второй страницы.")

# Логика основного приложения
def main():
    title_text = st.empty()


    pages_name = [
        'Главная',
        'Задача N тел'
    ]

    # Радиокнопки для выбора страницы
    selected_page = st.radio(
        "Перейти на страницу:",
        pages_name,
        index=0  # Предустановленный выбор (0 - "Главная")
    )

    # Отображение нужной страницы
    if selected_page == pages_name[0]:
        title_text.title("Добро пожаловать!")
        home_page()
    elif selected_page == pages_name[1]:
        title_text.title("Задача N тел")
        nBody.run_n_body()
    elif selected_page == "Страница 2":
        page_two()

# Запуск приложения
if __name__ == "__main__":
    main()