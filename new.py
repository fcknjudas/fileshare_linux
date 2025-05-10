def run_attempt(attempt):
    print(f"\n=== Попытка {attempt}/{MAX_FAILED_ATTEMPTS} ===")

    if not os.path.exists(CRX_PATH):
        print(f"Ошибка: Файл расширения {CRX_PATH} не найден!")
        return False

    # Создаем уникальный профиль (только если будем использовать вариант с профилем)
    profile_name = f"profile_{uuid.uuid4()}"
    profile_path = os.path.join(BASE_PROFILE_DIR, profile_name)
    os.makedirs(profile_path, exist_ok=True)
    print(f"Создан новый профиль: {profile_path}")

    # Пробуем сначала вариант без профиля, если не получится - с профилем
    for use_profile in [False, True]:
        driver = None
        try:
            print(f"\nПопытка с {'профилем' if use_profile else 'временным каталогом'}")
            driver = setup_driver(profile_path, use_profile=use_profile)
            print("Драйвер успешно инициализирован")
            
            # Остальной код остается без изменений...
            # ... (основной поток выполнения)
            
            return True  # Если выполнение дошло до этой точки
            
        except WebDriverException as e:
            print(f"Ошибка WebDriver (use_profile={use_profile}): {str(e)}")
            if driver:
                driver.save_screenshot(f"error_{'profile' if use_profile else 'temp'}_{attempt}.png")
            if use_profile:  # Если это была вторая попытка (с профилем)
                return False
            continue  # Пробуем следующий вариант
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
                if use_profile:  # Очищаем только если использовали профиль
                    cleanup_profile(profile_path)
    
    return False  # Если оба варианта не сработали
