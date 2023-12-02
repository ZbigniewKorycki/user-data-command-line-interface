from argparse import Namespace, ArgumentParser
from actions import Actions

parser = ArgumentParser()

commands_list = [
    "print-all-accounts",
    "print-oldest-account",
    "group-by-age",
    "print-children",
    "find-similar-children-by-age",
    "create-database",
]

parser.add_argument("command", type=str, help="enter command")
parser.add_argument("--login", type=str, help="input user login")
parser.add_argument("--password", type=str, help="input user password")
args: Namespace = parser.parse_args()

if args.command in commands_list:
    action = Actions(login=args.login, password=args.password)

    if args.command == "print-all-accounts":
        action.print_all_accounts()

    elif args.command == "print-oldest-account":
        action.print_oldest_account()

    elif args.command == "group-by-age":
        action.group_children_by_age()

    elif args.command == "print-children":
        action.get_user_children()

    elif args.command == "find-similar-children-by-age":
        action.find_users_with_similar_children_by_age()

    elif args.command == "create-database":
        pass
else:
    print("Unrecognized command")
