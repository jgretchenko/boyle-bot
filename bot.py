import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

API_TOKEN = '7789724358:AAGYxOCOKEhO3FA7lODT2glHI-7M3-xaAyc'  # Замените на ваш токен
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Логирование
logging.basicConfig(level=logging.INFO)

# Список критериев
criteria = [
    "Внешний вид", "Текстура", "Аромат", "Вкус", "Гарнир", "Соус",
    "Подача", "Сервировка", "Температура подачи", "Сочетание с напитком",
    "Общая стоимость блюда", "Рот-комфорт"
]

# Хранение оценок и информации
user_scores = {}
current_user = None
current_criterion_index = 0
message_history = []  # Список для хранения ID сообщений, которые нужно удалить
user_message_history = []  # Список для хранения ID сообщений пользователя
dish_name = None  # Хранение названия блюда


# Функция для удаления сообщений
async def delete_previous_messages(chat_id):
    # Удаляем сообщения бота
    for message_id in message_history:
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception as e:
            logging.error(f"Не удалось удалить сообщение бота: {e}")

    # Удаляем сообщения пользователя
    for message_id in user_message_history:
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception as e:
            logging.error(f"Не удалось удалить сообщение пользователя: {e}")


# Функция для отправки итогового сообщения
async def send_final_scores(message, chat_id):
    global user_scores, criteria, dish_name
    total_score = 0
    count = 0
    result_message = f"Оценка блюда: *{dish_name}*\n\n"  # Добавляем название блюда

    for i, criterion in enumerate(criteria):
        score = user_scores[i] if i in user_scores else "—"
        result_message += f"{criterion}: {score}\n"
        if score != "—":
            total_score += score
            count += 1

    if count > 0:
        average_score = total_score / count
        result_message += f"\n**Общая оценка: {average_score:.2f}**"
    else:
        result_message += "\n**Общая оценка: —**"

    # Отправляем итоговое сообщение и удаляем старые сообщения
    final_message = await bot.send_message(chat_id, result_message, parse_mode=ParseMode.MARKDOWN)
    await delete_previous_messages(chat_id)

    # Запоминаем ID нового сообщения для удаления в будущем
    message_history.append(final_message.message_id)

    # Очищаем данные пользователя
    user_scores = {}
    dish_name = None  # Очищаем название блюда


# Хендлер для старта
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    global current_user, current_criterion_index, dish_name
    current_user = message.from_user.id
    current_criterion_index = 0
    user_scores.clear()
    message_history.clear()
    user_message_history.clear()

    # Отправляем первое сообщение с просьбой ввести название блюда
    msg = await message.answer("Привет! Оцените блюдо. Пожалуйста, введите название блюда:")
    message_history.append(msg.message_id)


# Хендлер для ввода названия блюда
@dp.message_handler()
async def handle_message(message: types.Message):
    global current_criterion_index, user_scores, current_user, dish_name

    # Сохраняем ID сообщения пользователя
    user_message_history.append(message.message_id)

    if current_criterion_index == 0:
        # Сохраняем название блюда
        dish_name = message.text
        msg = await message.answer(f"Блюдо '{dish_name}' сохранено. Теперь оцените его по следующим критериям:")
        message_history.append(msg.message_id)

        # Переходим к первому критерию
        await ask_for_criteria(message)

    elif current_criterion_index < len(criteria):
        # Ожидаем оценку
        score = await get_user_score(message)

        if score is not None:
            # Если введено корректное число, сохраняем оценку
            user_scores[current_criterion_index - 1] = score
            await ask_for_criteria(message)
        else:
            # Если введена ошибка, просим снова
            msg = await message.answer(
                f"Пожалуйста, введите оценку от 1 до 10 для '{criteria[current_criterion_index - 1]}'.")
            message_history.append(msg.message_id)

    else:
        # Завершаем оценку и отправляем итоговое сообщение
        await send_final_scores(message, message.chat.id)
        current_criterion_index = 0  # Сброс состояния
        current_user = None  # Сброс пользователя


# Функция для получения оценки пользователя с проверкой на корректность
async def get_user_score(message):
    try:
        score = int(message.text)
        if 1 <= score <= 10:
            return score
        else:
            return None
    except ValueError:
        return None


# Функция для отправки следующего критерия
async def ask_for_criteria(message):
    global current_criterion_index
    if current_criterion_index < len(criteria):
        criterion = criteria[current_criterion_index]
        msg = await message.answer(f"Оцените {criterion} (1-10):")
        message_history.append(msg.message_id)
        current_criterion_index += 1
    else:
        # Завершаем оценку
        await send_final_scores(message, message.chat.id)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
