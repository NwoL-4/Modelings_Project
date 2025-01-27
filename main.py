import streamlit as st
import pages.N_body as nBody
import pages.heat_equation as heatEq

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
        'Задача N тел',
        'Уравнение теплопроводности'
    ]

    # Радиокнопки для выбора страницы
    selected_page = st.radio(
        "Перейти на страницу:",
        pages_name,
        index=0  # Предустановленный выбор (0 - "Главная")
    )

    # Отображение нужной страницы
    match selected_page:
        case 'Главная':
            title_text.title('Добро пожаловать')
        case 'Задача N тел':
            title_text.title(selected_page)
            nBody.run_n_body()
        case 'Уравнение теплопроводности':
            title_text.title(selected_page)
            heatEq.run_heat_equation()


# Запуск приложения
if __name__ == "__main__":
    main()