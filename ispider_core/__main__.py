# ispider_core/__main__.py
import sys
from ispider_core.utils.menu import menu
from ispider_core.utils.logger import LoggerFactory
from ispider_core.crawlers.stage1_seed_fetcher import


if __name__ == "__main__":
    args = menu()
    if args.stage is None:
        print("No valid stage selected. Use -h for help.")
        sys.exit()

    if args.stage == 'stage1':
        # Call stage1 function here
        print("Running Stage 1...")
    elif args.stage == 'stage2':
        # Call stage2 function here
        print("Running Stage 2...")
    elif args.stage == 'stage3':
        # Call stage3 function here
        print("Running Stage 3...")
    elif args.stage == 'stage4':
        # Call stage4 function here
        print("Running Stage 4...")


