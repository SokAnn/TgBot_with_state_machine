"""
Telegram Bot with State Machine
"""

import telebot
from transitions import Machine, State
import config

# states of state machine
states = ['init', 'begin', 'large_pizza', 'small_pizza', 'cash', 'non_cash', 'end']
pizza_states = [State(states[i]) for i in range(len(states))]
# transitions of state machine
pizza_transitions = [{'trigger': 'start_work', 'source': 'init', 'dest': 'begin'},
                     {'trigger': 'choice_of_large_pizza', 'source': 'begin', 'dest': 'large_pizza'},
                     {'trigger': 'choice_of_small_pizza', 'source': 'begin', 'dest': 'small_pizza'},
                     {'trigger': 'large_pizza_and_choice_of_cash', 'source': 'large_pizza', 'dest': 'cash'},
                     {'trigger': 'large_pizza_and_choice_of_non_cash', 'source': 'large_pizza', 'dest': 'non_cash'},
                     {'trigger': 'small_pizza_and_choice_of_cash', 'source': 'small_pizza', 'dest': 'cash'},
                     {'trigger': 'small_pizza_and_choice_of_non_cash', 'source': 'small_pizza', 'dest': 'non_cash'},
                     {'trigger': 'payment_in_cash', 'source': 'cash', 'dest': 'end'},
                     {'trigger': 'payment_in_non_cash', 'source': 'non_cash', 'dest': 'end'},
                     {'trigger': 'restart', 'source': 'end', 'dest': 'init'}]
# bot questions
list_questions = ['Какую пиццу Вы хотите заказать: большую или маленькую?',
                  'Как Вы будете платить?',
                  'Вы хотите %s пиццу, оплата - %s?',
                  'Спасибо за заказ!']

# init bot
bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def start_msg(message):
    bot.send_message(message.chat.id, f'Доброго времени суток, любитель пиццы!')
    # send sticker
    hi_sticker = open('stickers/yoda.tgs', 'rb')
    bot.send_sticker(message.chat.id, hi_sticker)
    bot.send_message(message.chat.id, 'Для того чтобы оформить заказ, напишите \'начать\'. '
                                      'Для получения справки введите команду /help')


@bot.message_handler(commands=['help'])
def help_msg(message):
    bot.send_message(message.chat.id, 'Данный бот ведет простой диалог с пользователем на тему оформления заказа пиццы.'
                                      '\nВ качестве возможных ответов на вопросы бота предусмотрены следующие ответы:\n'
                                      '\t- пицца может быть большой или маленькой;\n\t- оплата может быть только '
                                      'наличкой или безналичкой;\n\t- в последнем вопросе бот должен получить ответ да '
                                      'или нет, если бот получает ответ да, то заказ считается оформленным, если ответ '
                                      'нет - бот просит пройти процедуру заполнения заказа ещё раз.')


@bot.message_handler(content_types='text')
def send_msg(message):
    global state_machine
    global user_answers
    if message.content_type == 'text':
        if my_model.is_init():
            if message.text.lower() == 'начать':
                user_answers = []
                state_machine.dispatch('start_work')  # init -> begin
                bot.send_message(message.chat.id, list_questions[0])
        elif my_model.is_begin():
            if message.text.lower() == 'большую':
                user_answers.append('большую')
                state_machine.dispatch('choice_of_large_pizza')  # begin -> large pizza
                bot.send_message(message.chat.id, list_questions[1])
            elif message.text.lower() == 'маленькую':
                user_answers.append('маленькую')
                state_machine.dispatch('choice_of_small_pizza')  # begin -> small pizza
                bot.send_message(message.chat.id, list_questions[1])
            else:
                bot.send_message(message.chat.id, "Такой пиццы у нас пока нет :(\nПопробуйте снова!")
        elif my_model.is_large_pizza() or my_model.is_small_pizza():
            if message.text.lower() == 'наличкой':
                user_answers.append('наличкой')
                if user_answers[0] == 'большую':
                    state_machine.dispatch('large_pizza_and_choice_of_cash')  # large pizza -> cash
                else:
                    state_machine.dispatch('small_pizza_and_choice_of_cash')  # small pizza -> cash
                bot.send_message(message.chat.id, list_questions[2] % (user_answers[0], user_answers[1]))
            elif message.text.lower() == 'безналичкой':
                user_answers.append('безналичкой')
                if user_answers[0] == 'большую':
                    state_machine.dispatch('large_pizza_and_choice_of_non_cash')  # large pizza -> non-cash
                else:
                    state_machine.dispatch('small_pizza_and_choice_of_non_cash')  # small pizza -> non-cash
                bot.send_message(message.chat.id, list_questions[2] % (user_answers[0], user_answers[1]))
            else:
                bot.send_message(message.chat.id, "Такой способ оплаты пока не предусмотрен или Вы неправильно написали"
                                                  " способ оплаты. Попробуйте снова!")
        elif my_model.is_cash() or my_model.is_non_cash():
            if message.text.lower() == 'да':
                if my_model.state == 'cash':
                    state_machine.dispatch('payment_in_cash')  # cash -> end
                elif my_model.state == 'non_cash':
                    state_machine.dispatch('payment_in_non_cash')  # non-cash -> end
                bot.send_message(message.chat.id, list_questions[3])
                state_machine.dispatch('restart')  # end -> init
            elif message.text.lower() == 'нет':
                bot.send_message(message.chat.id, "Возможно что-то пошло не так :(\nОформите заказ заново. Для "
                                                  "оформления нового заказа напишите \'начать\'")
                if my_model.state == 'cash':
                    state_machine.dispatch('payment_in_cash')  # cash -> end
                elif my_model.state == 'non_cash':
                    state_machine.dispatch('payment_in_non_cash')  # non-cash -> end
                state_machine.dispatch('restart')  # end -> init
            else:
                bot.send_message(message.chat.id, "Подразумевается ответ да/нет!")


class MyMachine(object):
    pass


if __name__ == "__main__":
    my_model = MyMachine()
    state_machine = Machine(model=my_model, states=pizza_states, transitions=pizza_transitions, initial='init')
    user_answers = []
    bot.polling(none_stop=True)
