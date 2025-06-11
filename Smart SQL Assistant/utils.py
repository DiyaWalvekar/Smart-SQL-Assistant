import matplotlib.pyplot as plt
import io
import base64
import pyttsx3
import json

def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def detect_chart_type(columns, data):
    if not columns or not data:
        return "bar"
    # Pie chart: one column categorical or two columns with small number of categories
    if isinstance(data[0][columns[0]], str):
        if len(columns) == 1 and len(data) <= 10:
            return "pie"
        elif len(columns) == 2 and isinstance(data[0][columns[1]], (int, float)) and len(data) <= 10:
            return "pie"

    # Scatter plot: both columns numeric
    if len(columns) >= 2:
        x, y = data[0][columns[0]], data[0][columns[1]]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return "scatter"

    # Line plot: both columns numeric and seem continuous
    if len(columns) == 2 and isinstance(data[0][columns[0]], (int, float)) and isinstance(data[0][columns[1]], (int, float)):
        return "line"

    # Histogram: one numeric column
    if len(columns) == 1 and isinstance(data[0][columns[0]], (int, float)):
        return "histogram"

    # Bar chart: default if none of the above
    return "bar"

def generate_visualization(data, columns):
    if not data or not columns:
        return None

    x_label = columns[0]
    y_label = columns[1] if len(columns) > 1 else None

    x = [row[x_label] for row in data]
    y = [row[y_label] for row in data] if y_label else None

    chart_type = detect_chart_type(columns, data)

    try:
        plt.figure(figsize=(10, 6))

        if chart_type == "bar":
            plt.bar(x, y, color="skyblue")
            plt.xlabel(x_label, fontsize=12)
            plt.ylabel(y_label, fontsize=12)

        elif chart_type == "pie":
            # Pie chart: Using the first column for labels and the second for values
            plt.pie(y if y else [1]*len(x), labels=x, autopct='%1.1f%%', startangle=140)
            plt.axis('equal')  # Equal aspect ratio ensures pie is drawn as a circle.

        elif chart_type == "scatter":
            plt.scatter(x, y, color="green")
            plt.xlabel(x_label, fontsize=12)
            plt.ylabel(y_label, fontsize=12)

        elif chart_type == "line":
            plt.plot(x, y, color="blue", marker='o')
            plt.xlabel(x_label, fontsize=12)
            plt.ylabel(y_label, fontsize=12)

        elif chart_type == "histogram":
            plt.hist(x, bins=10, color="orange")
            plt.xlabel(x_label, fontsize=12)
            plt.ylabel("Frequency", fontsize=12)

        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(fontsize=10)
        plt.title(f"Auto-generated {chart_type.capitalize()} Graph", fontsize=14)
        plt.tight_layout(pad=2.0)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()
        plt.close()

        return f"data:image/png;base64,{encoded}"

    except Exception as e:
        print(f"Chart generation failed: {e}")
        return None


def generate_chart_data(data, columns):
    if not data or len(columns) < 2:
        return json.dumps({})

    try:
        labels = [str(row[columns[0]]) for row in data]
        values = [float(row[columns[1]]) for row in data]
        chart_data = {
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": columns[1],
                    "data": values,
                    "backgroundColor": "rgba(0,123,255,0.6)"
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {"beginAtZero": True}
                }
            }
        }
        return json.dumps(chart_data)
    except Exception as e:
        print(f"Chart generation failed: {e}")
        return json.dumps({})


def convert_to_html_table(data, columns):
    html = "<table><thead><tr>"
    html += ''.join([f"<th>{col}</th>" for col in columns]) + "</tr></thead><tbody>"
    for row in data:
        html += "<tr>" + ''.join([f"<td>{row.get(col, '')}</td>" for col in columns]) + "</tr>"
    html += "</tbody></table>"
    return html


def generate_insights(data, columns):
    if not data or not columns:
        return "No data to analyze."

    insights = []
    if isinstance(data[0][columns[0]], (int, float)):
        values = [row[columns[0]] for row in data]
        avg = sum(values) / len(values)
        insights.append(f"Average {columns[0]}: {avg:.2f}")
        insights.append(f"Max {columns[0]}: {max(values)}")
        insights.append(f"Min {columns[0]}: {min(values)}")
    else:
        unique = set(row[columns[0]] for row in data)
        insights.append(f"Unique {columns[0]} values: {len(unique)}")

    # Return insights as a string
    return "\n".join(insights)
