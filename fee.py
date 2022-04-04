
def get_basic_fee(profit_percent):

    percent_increase = 0.02

    if profit_percent < 0:
        return 0

    if profit_percent > 5.00:
        profit_percent = 5.00
    return profit_percent * percent_increase


def get_user_fee_percent(profit_percent, fee_level):
    basic_fee = get_basic_fee(profit_percent)
    return basic_fee * fee_level


def get_user_fee(user_fee_percent, user_investment):
    return user_investment * user_fee_percent


def get_user_balance_before_fee(profit_percent, user_investment):
    return user_investment + user_investment * profit_percent


def get_user_fee_level(user_investment):
    if user_investment >= 50000:
        return 1
    if user_investment >= 30000:
        return 2
    if user_investment >= 10000:
        return 3
    if user_investment >= 5000:
        return 4
    if user_investment >= 1000:
        return 5

def main():
    start_balance = float(input("\nPlease Enter Envision Account Start Balance: "))
    end_balance = float(input("Please Enter Envision Account End Balance: "))
    user_deposit = float(input("Please Enter User Deposit: "))

    if user_deposit < 1000:
        print("\nUser investment is lower than minimum requirement")
        return


    profit_percent = (end_balance - start_balance)/ start_balance
    user_fee_level = get_user_fee_level(user_deposit)
    user_fee_percent = get_user_fee_percent(profit_percent, user_fee_level)
    user_balance_before_fee = get_user_balance_before_fee(profit_percent, user_deposit)
    user_profit_before_fee = user_balance_before_fee - user_deposit
    user_due_fee = get_user_fee(user_fee_percent, user_profit_before_fee)
    user_balance_after_fee = user_balance_before_fee - user_due_fee
    user_profit = user_balance_after_fee - user_deposit
    print("\n=============================================================================="
          "\nUser investment: %f"
          "\nUser fee level: %d"
          "\nUser fee percentage:%f"
          "\nUser Balance Before Fee: %f"
          "\nUser due fee: %f"
          "\nUser Balance After Fee: %f"
          "\nUser Profit: %f"
          "\n=============================================================================="% (
        user_deposit,
        user_fee_level,
        user_fee_percent,
        user_balance_before_fee,
        user_due_fee,
        user_balance_after_fee,
        user_profit
    ))

if __name__ == '__main__':
    main()