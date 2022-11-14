import numpy as np
import json  # подключили библиотеку для работы с json
from pprint import pprint  # подключили Pprint для красоты выдачи текста

with open('tyumen_cafe.json', 'r', encoding='utf-8') as f:  # открыли файл с данными
    restoraunts = (json.load(f))  # загнали все, что получилось в переменную


key = 'type'


class User(object):
    id
    location = ""
    history = []  # выборы ресторанов

    def __init__(self, id=0, location="", history=[]):
        """Constructor"""
        self.id = id
        self.location = location
        self.history = history

    def to_string(self):
        print("Пользователь id = ", self.id, "находится ", self.location, "выбирал такие рестораны: ", self.history)


def get_current_user(id):
    with open('users.json', 'r+', encoding='utf-8') as f:  # открыли файл с данными
        text = json.load(f)  # загнали все, что получилось в переменную
        users_text = (text)
        flag = False
        for i in range(len(users_text)):
            if (int(users_text[i]["UserId"]) == id):
                flag = True
                u1 = User(id, users_text[i]["Location"], users_text[i]["History"])

        if (flag == False):  # если такого пользователя нет, то перезаписываем файл с пользователями и добавляем данные
            new_user = {}
            new_user["UserId"] = len(users_text) + 1
            new_user["Location"] = "Тюмень"  # тут Катя отдает местоположение
            new_user["History"] = []

            text.append(new_user)

            f.seek(0)
            json.dump(text, f)
            get_current_user(len(users_text) + 1)  # заполнили таблицу и вновь ищем пользователя, возвращаем объект
        return u1


u1 = get_current_user(1)
u1.to_string()

# выбираем рестораны которые пользователь выбирал
selected_restoraunts = []
for i in u1.history:
    selected_restoraunts.append(restoraunts[i][key])

# изменим значки долларов из датасета в тип чека для удобства
for i in range(len(selected_restoraunts)):

    if selected_restoraunts[i][0] == "$$ - $$$":
        selected_restoraunts[i][0] = "Средний"
    if selected_restoraunts[i][0] == "$$$$":
        selected_restoraunts[i][0] = "Высокий"
    if selected_restoraunts[i][0] == '$':
        selected_restoraunts[i][0] = "Низкий"

user_vector_checks = [selected_restoraunts[i][0] for i in range(len(selected_restoraunts))]
user_vector_types = []
for i in range(len(selected_restoraunts)):
    user_vector_types.append(selected_restoraunts[i][1:])

# получили вектора истории выборов типа кухонь и тип выбранных чеков пользоватея
print(user_vector_checks)
print(user_vector_types)

# для работы нам нужна именно строка из признаков истории пользователя, а не массив, каким он создается
user_vector_types_str = ""
for i in range(len(user_vector_types)):
    for j in range(len(user_vector_types[i])):
        user_vector_types_str += str(user_vector_types[i][j]) + " "

print(user_vector_types_str)

# чтобы TfidfVectorizer ниже в коде работал надо user_vector_types из листа листов сделать листом string

user_vector_types = [str(i) for i in user_vector_types]
print(user_vector_types)
from sklearn.feature_extraction.text import CountVectorizer

vectorizer1 = CountVectorizer(lowercase=True)
X_checks = vectorizer1.fit_transform(user_vector_checks)
print(X_checks)
print(vectorizer1.vocabulary_)
print(X_checks.toarray())


from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer2 = TfidfVectorizer(norm = "l1", stop_words=["для", "подходит"])

vectorizer2.fit(user_vector_types)
# summarize
print(vectorizer2.vocabulary_)
#print(vectorizer2.idf_) #обратная частота встречаемости слова

print(vectorizer2.get_feature_names_out())
# кодируем строку из типов кухонь обученным объектом класса
vector2 = vectorizer2.transform([user_vector_types_str])
print(vector2.shape)
print(user_vector_types_str)
user_vertor_types = vector2.toarray()
print(user_vertor_types)# чем реже слово тем оно значимей и значит значение tf-idf дает больше
restoraunts_for_recommend = []
for i in range(0, 10):
    if (i not in u1.history):
        restoraunts_for_recommend.append(restoraunts[i][key])

# изменим значки долларов из датасета в тип чека
for i in range(len(restoraunts_for_recommend)):

    if restoraunts_for_recommend[i][0] == "$$ - $$$":
        restoraunts_for_recommend[i][0] = "Средний"
    if restoraunts_for_recommend[i][0] == "$$$$":
        restoraunts_for_recommend[i][0] = "Высокий"
    if restoraunts_for_recommend[i][0] == '$':
        restoraunts_for_recommend[i][0] = "Низкий"
restoraunts_for_recommend1 = []
for i in range(len(restoraunts_for_recommend)):
    restoraunts_for_recommend1.append(str(restoraunts_for_recommend[i][1:]))

print(restoraunts_for_recommend1)

vector2 = vectorizer2.transform(restoraunts_for_recommend1)
restoraunts_vector_types = vector2.toarray()
print(restoraunts_vector_types)
def cos_distance(data1, data2):
    sum = 0
    sumA = 0
    sumB = 0
    for i in range(len(user_vertor_types[0])):
        sum+=(data1[i] * data2[0][i])
        sumA+=data1[i]**2
        sumB+=data2[0][i]**2
    return sum/np.sqrt(sumA)*np.sqrt(sumB)

#создаем лист из множества, где первый элемент - индекс ресторана, а второй элемент - расстрояние вектора ресторана до вектора пользователя
distances_restoraunt = [ (i, cos_distance(restoraunts_vector_types[i], user_vertor_types )) for i in range(len(restoraunts_for_recommend))]
#сортируем вектор по убыванию, первые элементы - наиболее похожие, дальше - наиболее различны
distances_restoraunt.sort(key=lambda elem: elem[1], reverse=True)
print(distances_restoraunt)
print()


print(user_vector_types_str)

#3 ресторана наиболее подходящие к вектору пользователя
for i in range(3):
  #показать что близки значения типов кухонь
  print(restoraunts[distances_restoraunt[i][0]][key])
  #уже на вывод
  print(restoraunts[distances_restoraunt[i][0]])

print()
#3 ресторана наименее подходящие к вектору пользователя
for i in range(3):
  #показать что близки значения типов кухонь
  print(restoraunts[distances_restoraunt[len(distances_restoraunt)-i-1][0]][key])
    #уже на вывод
  print(restoraunts[distances_restoraunt[len(distances_restoraunt)-i-1][0]])
