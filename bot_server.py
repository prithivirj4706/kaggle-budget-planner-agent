from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)

# In-memory transaction storage
transactions = []
budgets = {
    'Groceries': 3000,
    'Dining': 2000,
    'Transport': 1500,
    'Entertainment': 1000,
    'Utilities': 2000,
    'Healthcare': 1500,
    'Shopping': 2500,
    'Education': 3000,
    'Other': 1000
}

categories = ['Groceries', 'Dining', 'Transport', 'Entertainment', 
              'Utilities', 'Healthcare', 'Shopping', 'Education', 'Other']

def categorize_transaction(description, amount):
    """Layer 3: AI Categorization Agent"""
    description_lower = description.lower()
    
    category_keywords = {
        'Groceries': ['grocery', 'mart', 'food', 'vegetables', 'store', 'bigmart', 'kirana'],
        'Dining': ['cafe', 'restaurant', 'lunch', 'dinner', 'food delivery', 'pizza', 'burger'],
        'Transport': ['uber', 'auto', 'fuel', 'bus', 'train', 'taxi', 'petrol', 'diesel'],
        'Entertainment': ['movie', 'cinema', 'game', 'netflix', 'spotify', 'concert'],
        'Utilities': ['electricity', 'water', 'phone', 'internet', 'bill', 'mobile'],
        'Healthcare': ['doctor', 'hospital', 'medicine', 'pharmacy', 'health', 'clinic'],
        'Shopping': ['amazon', 'flipkart', 'clothes', 'shoe', 'apparel', 'mall'],
        'Education': ['school', 'college', 'course', 'book', 'tuition', 'class'],
    }
    
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in description_lower:
                return category
    
    return 'Other'

def get_budget_status():
    """Layer 4: Budget Analysis Agent"""
    spending_by_category = {}
    for tx in transactions:
        cat = tx['category']
        spending_by_category[cat] = spending_by_category.get(cat, 0) + tx['amount']
    
    status = {}
    for category, budget in budgets.items():
        spent = spending_by_category.get(category, 0)
        remaining = budget - spent
        percentage = (spent / budget * 100) if budget > 0 else 0
        status[category] = {
            'budget': budget,
            'spent': spent,
            'remaining': remaining,
            'percentage': round(percentage, 2),
            'status': 'OK' if percentage <= 80 else 'WARNING' if percentage <= 100 else 'EXCEEDED'
        }
    return status

def process_message(user_message):
    """Process user messages and return bot responses"""
    message_lower = user_message.lower()
    
    # Extract transaction if user mentions adding one
    if any(word in message_lower for word in ['add', 'spent', 'expense', 'transaction']):
        # Try to extract amount and description
        amount_match = re.search(r'(\d+)', user_message)
        if amount_match:
            amount = int(amount_match.group(1))
            description = user_message
            category = categorize_transaction(description, amount)
            transaction = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'description': description,
                'amount': amount,
                'category': category,
                'method': 'Card'
            }
            transactions.append(transaction)
            return f"✅ Transaction added!\nAmount: ₹{amount}\nCategory: {category}\nDescription: {description}\n\nYour budget status updated."
    
    # Budget inquiry
    if 'budget' in message_lower or 'spending' in message_lower:
        status = get_budget_status()
        response = "💰 **BUDGET STATUS**\n\n"
        total_spent = sum([tx['amount'] for tx in transactions])
        response += f"Total Spent: ₹{total_spent}\n\n"
        for category, info in status.items():
            status_icon = '🟢' if info['status'] == 'OK' else '🟡' if info['status'] == 'WARNING' else '🔴'
            response += f"{status_icon} {category}: ₹{info['spent']}/₹{info['budget']} ({info['percentage']}%)\n"
        return response
    
    # Spending summary
    if 'summary' in message_lower or 'total' in message_lower or 'how much' in message_lower:
        if not transactions:
            return "📊 No transactions yet. Add some expenses to see your summary!"
        
        spending_by_category = {}
        total_spent = 0
        for tx in transactions:
            cat = tx['category']
            spending_by_category[cat] = spending_by_category.get(cat, 0) + tx['amount']
            total_spent += tx['amount']
        
        response = "📊 **SPENDING SUMMARY**\n\n"
        response += f"Total Expenses: ₹{total_spent}\n\n"
        response += "**Top Categories:**\n"
        sorted_cats = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (cat, amount) in enumerate(sorted_cats, 1):
            response += f"{i}. {cat}: ₹{amount}\n"
        return response
    
    # Top spending
    if 'top' in message_lower or 'highest' in message_lower:
        if not transactions:
            return "No transactions recorded yet."
        sorted_tx = sorted(transactions, key=lambda x: x['amount'], reverse=True)[:3]
        response = "🏆 **TOP EXPENSES**\n\n"
        for i, tx in enumerate(sorted_tx, 1):
            response += f"{i}. ₹{tx['amount']} - {tx['description']} ({tx['category']})\n"
        return response
    
    # Financial insights
    if 'insight' in message_lower or 'advice' in message_lower or 'tip' in message_lower:
        status = get_budget_status()
        exceeded = [cat for cat, info in status.items() if info['status'] == 'EXCEEDED']
        warning = [cat for cat, info in status.items() if info['status'] == 'WARNING']
        
        if exceeded:
            return f"⚠️ **ALERT**: You've exceeded budget in {', '.join(exceeded)}. Cut back on these categories!\n\nTip: Try to reduce discretionary spending and focus on essentials."
        elif warning:
            return f"📢 **WARNING**: You're near budget limit in {', '.join(warning)}.\n\nTip: Be careful with upcoming expenses in these categories."
        else:
            return f"✨ **Great Job!** Your spending is under control.\n\nTip: Continue tracking and maintain your budget discipline!"
    
    # Recent transactions
    if 'recent' in message_lower or 'recent transactions' in message_lower or 'history' in message_lower:
        if not transactions:
            return "📋 No transactions yet. Add some to see your history!"
        recent = transactions[-5:]
        response = "📋 **RECENT TRANSACTIONS**\n\n"
        for tx in reversed(recent):
            response += f"₹{tx['amount']} - {tx['description']}\nCategory: {tx['category']}\nDate: {tx['date']}\n\n"
        return response
    
    # Help/Info
    if 'help' in message_lower or 'command' in message_lower or 'what' in message_lower:
        return "🤖 **BUDGET BOT COMMANDS**\n\nYou can ask me:\n" + \
               "• 'Add ₹500 for groceries' - Add a transaction\n" + \
               "• 'Show budget status' - View budget progress\n" + \
               "• 'Spending summary' - Get expense overview\n" + \
               "• 'Top expenses' - See highest spending\n" + \
               "• 'Recent transactions' - View transaction history\n" + \
               "• 'Give me insights' - Get financial advice\n" + \
               "• 'Help' - Show this menu"
    
    # Default response
    return "👋 Hi! I'm your Budget Planner Bot. Type 'help' to see what I can do!\n\n" + \
           "Or try:\n• 'Add ₹1000 for dining'\n• 'Show budget status'\n• 'Spending summary'"

@app.route('/')
def index():
    return render_template('bot_ui.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    # Process the message with all 5 layers
    bot_response = process_message(user_message)
    
    return jsonify({
        'response': bot_response,
        'transactions': len(transactions),
        'status': 'success'
    })

@app.route('/api/data', methods=['GET'])
def get_data():
    """Layer 5: Dashboard Agent - Return visualization data"""
    spending_by_category = {}
    for tx in transactions:
        cat = tx['category']
        spending_by_category[cat] = spending_by_category.get(cat, 0) + tx['amount']
    
    return jsonify({
        'transactions': transactions,
        'spending_by_category': spending_by_category,
        'budget_status': get_budget_status(),
        'total_transactions': len(transactions),
        'total_spent': sum([tx['amount'] for tx in transactions])
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
