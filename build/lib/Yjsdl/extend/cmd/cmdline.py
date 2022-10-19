import sys
from os.path import dirname, join
from ..cmd import create_builder


def _print_commands():
    """
    @summery: copy form https://github.com/zaoxg/ReSpiderFramework/blob/main/ReSpider/cmd/cmdline.py
    """
    with open(join(dirname(dirname(dirname(__file__))), "VERSION"), "rb") as f:
        version = f.read().decode("ascii").strip()

    print("Yjsdl {}".format(version))
    print("\nUsage:")
    print("  Yjsdl <command> [options] [args]\n")
    print("Available commands:")
    cmds = {
        "create": "create project、spider",
    }
    for cmdname, cmdclass in sorted(cmds.items()):
        print("  %-13s %s" % (cmdname, cmdclass))

    print('\nUse "Yjsdl <command> -h" to see more info about a command')


def execute():
    args = sys.argv
    if len(args) < 2:
        _print_commands()
        return

    command = args.pop(1)
    if command == "create":
        create_builder.main()
    else:
        _print_commands()


if __name__ == '__main__':
    execute()
