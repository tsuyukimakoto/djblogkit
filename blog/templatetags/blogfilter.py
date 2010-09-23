from django.template import Library

register = Library()

def truncatelines(value, arg) :
    if value == None or value == "" :
        return ""
    try :
        lines = int(arg)
    except ValueError: # invalid literal for int()
        return value # Fail silently.
    try :
        line_list = value.rstrip().split('\n')[:lines]
        result = ""
        for line in line_list :
            result += line + "\n"
        result = result.rstrip()
        return result
    except :
        return value

register.filter('truncatelines', truncatelines)

def to_oneline(value) :
    if value == None or value == "" :
        return ""
    line_list = value.rstrip().split('\n')
    result = ""
    for line in line_list :
        result += line
    result = result.rstrip()
    return result

register.filter('to_oneline', to_oneline)

