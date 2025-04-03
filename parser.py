import time
import json
import csv
import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
username = os.getenv("INSTA_USERNAME")
password = os.getenv("INSTA_PASSWORD")

def parse_instagram_profile(profile_url):
    gecko_driver_path = "/Users/mustafodavlatov/Downloads/geckodriver"  # Замените на реальный путь
    service = Service(gecko_driver_path)
    driver = webdriver.Firefox(service=service)

    try:
        # Открываем страницу входа
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)

        # Логинимся
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys(username)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        time.sleep(10)

        # Переходим на страницу профиля
        driver.get(profile_url)
        time.sleep(5)

        # Ждём загрузки контента
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h2"))
        )

        # Прокручиваем страницу для загрузки постов
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        # Получаем HTML-код страницы
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        # Извлекаем основные метрики профиля
        metrics_elements = soup.find_all('span', class_='html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs')
        if len(metrics_elements) < 2:
            raise Exception("Не удалось найти элементы с метриками.")

        followers = metrics_elements[1].get_text(strip=True) if metrics_elements else "Не найдено"
        posts = metrics_elements[0].get_text(strip=True) if metrics_elements else "Не найдено"

        # Ищем все посты
        post_elements = soup.find_all("div", class_="x1lliihq")

        posts_data = []
        for post in post_elements:
            try:
                # Описание поста
                img_tag = post.find("img")
                caption = img_tag["alt"][:100] if img_tag and "alt" in img_tag.attrs else "Без описания"

                # Количество лайков
                likes_element = post.find("span", class_="x1e558r4")  # Селектор для лайков
                likes = int(likes_element.text.replace(",", "").strip()) if likes_element else 0

                # Количество комментариев
                comments_element = post.find("span", class_="x1lliihq x1n2onr6")  # Селектор для комментариев
                comments = int(comments_element.text.replace(",", "").strip()) if comments_element else 0

                # Дата публикации
                date_element = post.find("time")  # Селектор для даты
                date = date_element["datetime"] if date_element else "Не найдено"

                # Сохраняем данные о посте
                posts_data.append({
                    "caption": caption,
                    "likes": likes,
                    "comments": comments,
                    "date": date
                })

                print(f"Caption: {caption}, Likes: {likes}, Comments: {comments}, Date: {date}")
            except Exception as e:
                print(f"Ошибка при обработке поста: {e}")

        # Формируем JSON-ответ
        profile_metrics = {
            "followers": followers,
            "posts": posts,
            "posts_data": posts_data
        }

        # Сохраняем данные в JSON-файл
        with open("profile_metrics.json", "w", encoding="utf-8") as f:
            json.dump(profile_metrics, f, ensure_ascii=False, indent=4)

        # Сохраняем данные в CSV-файл
        with open("instagram_posts.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter='\t')
            writer.writerow(["Описание поста", "Лайки", "Комментарии", "Дата публикации"])
            for post in posts_data:
                writer.writerow([post["caption"], post["likes"], post["comments"], post["date"]])

        return profile_metrics

    finally:
        driver.quit()

# Запуск парсера
profile_url = "https://www.instagram.com/example/"  # Укажите URL профиля
try:
    data = parse_instagram_profile(profile_url)
    print(json.dumps(data, ensure_ascii=False, indent=4))
except Exception as e:
    print("Ошибка:", e)