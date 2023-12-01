import cv2
from deepface import DeepFace
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

TOKEN = '6668204272:AAEB-jUZuEyDuOnDEjaDRJKzYvryJ6Qjw7E'
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
model = DeepFace.build_model("Emotion")
emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']


async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=None
    )


async def start_conversation(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hi! I will ask you some questions.")
    await ask_question(update, context)


async def ask_photo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('This is the ask_photo command.')


async def show_menu(update: Update, context: CallbackContext) -> None:
    # Define the menu buttons
    keyboard = [
        [InlineKeyboardButton("/start", callback_data='start')],
        [InlineKeyboardButton("/start_conversation", callback_data='start_conversation')],
        [InlineKeyboardButton("/ask_photo", callback_data='ask_photo')],
    ]

    # Create the menu markup
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the menu with the buttons
    await update.message.reply_text('Choose a command:', reply_markup=reply_markup)


async def handle_menu_button(update: Update, context: CallbackContext) -> None:
    # Define the options list
    options = [
        "/start",
        "/start_conversation",
        "/ask_photo",
    ]

    # Create a custom keyboard with the options
    keyboard = [[KeyboardButton(option)] for option in options]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    # Send the options list as a pop-up when the button is tapped
    await update.message.reply_text('Choose a command:', reply_markup=reply_markup)


async def handle_images(update: Update, context: CallbackContext) -> None:
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file = await context.bot.get_file(file_id)

        photo_path = 'received_image.jpg'
        await file.download_to_drive(photo_path)

        image = cv2.imread(photo_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        emotions_detected = []
        for (x, y, w, h) in faces:
            face_roi = gray[y:y + h, x:x + w]
            resized_face = cv2.resize(face_roi, (48, 48), interpolation=cv2.INTER_AREA)
            normalized_face = resized_face / 255.0
            reshaped_face = normalized_face.reshape(1, 48, 48, 1)
            preds = model.predict(reshaped_face)[0]
            emotion_idx = preds.argmax()
            emotion = emotion_labels[emotion_idx]
            emotions_detected.append(emotion)

            # Draw rectangle around face and label with predicted emotion
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(image, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        # Save the image with rectangles
        output_path = 'image_with_faces.jpg'
        cv2.imwrite(output_path, image)
        with open(output_path, 'rb') as photo:
            await update.message.reply_photo(photo, caption=f'Emotions detected: {", ".join(emotions_detected)}')

    else:
        await update.message.reply_text('Please send an image.')


async def ask_question(update: Update, context: CallbackContext) -> None:
    questions = ["What is your favorite color?", "How often do you exercise?"]
    for question in questions:
        await update.message.reply_text(question)
        context.user_data[question] = ["Green", "Blue", "Pink"]


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start_conversation", start_conversation))
    application.add_handler(CommandHandler("ask_photo", ask_photo))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(MessageHandler(filters.PHOTO, handle_images))
    application.add_handler(MessageHandler(filters.TEXT, handle_menu_button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
