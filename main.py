import ast
import os
import chardet


class MetricCalculator(ast.NodeVisitor):
    def __init__(self):
        self.classes = {}  # Зберігає інформацію про класи та їх базові класи
        self.inheritance_tree = {}  # Зберігає дерево спадковості класів
        self.methods = {}  # Зберігає методи для кожного класу
        self.attributes = {}  # Зберігає атрибути для кожного класу
        self.couplings = set()  # Зберігає зв'язки між класами
        self.overridden_methods = set()  # Зберігає перевизначені методи

    def visit_ClassDef(self, node):
        class_name = node.name
        base_classes = [base.id for base in node.bases if isinstance(base, ast.Name)]
        self.classes[class_name] = base_classes
        self.methods[class_name] = []
        self.attributes[class_name] = []

        for base in base_classes:
            if base not in self.inheritance_tree:
                self.inheritance_tree[base] = []
            self.inheritance_tree[base].append(class_name)

        for body_item in node.body:
            if isinstance(body_item, ast.FunctionDef):
                self.methods[class_name].append(body_item.name)
                for base in base_classes:
                    if body_item.name in self.methods.get(base, []):
                        self.overridden_methods.add(body_item.name)
            elif isinstance(body_item, ast.Assign):
                for target in body_item.targets:
                    if isinstance(target, ast.Name):
                        self.attributes[class_name].append(target.id)
                    elif isinstance(target, ast.Attribute):
                        attr_class = target.value.id if isinstance(target.value, ast.Name) else None
                        if attr_class and attr_class in self.classes:
                            self.couplings.add((class_name, attr_class))

        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            attr_class = node.value.id
            if attr_class in self.classes:
                current_class = getattr(self, 'current_class', None)
                if current_class:
                    self.couplings.add((current_class, attr_class))
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        current_class = getattr(self, 'current_class', None)
        if current_class:
            for stmt in node.body:
                self.visit(stmt)
        self.generic_visit(node)

    def calculate_dit(self, class_name, depth=0):
        base_classes = self.classes.get(class_name, [])
        if not base_classes:
            return depth
        return max(self.calculate_dit(base, depth + 1) for base in base_classes)

    def calculate_noc(self, class_name):
        return len(self.inheritance_tree.get(class_name, []))

    def calculate_mood_metrics(self):
        total_methods = sum(len(methods) for methods in self.methods.values())
        total_attributes = sum(len(attrs) for attrs in self.attributes.values())
        if total_methods == 0:
            total_methods = 1
        if total_attributes == 0:
            total_attributes = 1

        inherited_methods = sum(len(self.methods.get(base, [])) for cls in self.classes for base in self.classes[cls])
        hidden_methods = sum(1 for cls in self.classes for method in self.methods[cls] if method.startswith('_') and method not in self.overridden_methods)
        hidden_attributes = sum(1 for cls in self.classes for attr in self.attributes[cls] if attr.startswith('_'))
        inherited_attributes = sum(len(self.attributes.get(base, [])) for cls in self.classes for base in self.classes[cls])

        mif = inherited_methods / total_methods
        mhf = hidden_methods / total_methods
        ahf = hidden_attributes / total_attributes
        aif = inherited_attributes / total_attributes
        pof = self.calculate_pof()
        cof = self.calculate_cof()

        return {
            "MIF": mif,  # Відношення успадкованих методів до загальної кількості методів
            "MHF": mhf,  # Відношення прихованих методів до загальної кількості методів
            "AHF": ahf,  # Відношення прихованих атрибутів до загальної кількості атрибутів
            "AIF": aif,  # Відношення успадкованих атрибутів до загальної кількості атрибутів
            "POF": pof,  # Відношення кількості поліморфних методів до загальної кількості методів
            "COF": cof   # Відношення кількості зв'язків між класами до загальної кількості можливих зв'язків
        }

    def calculate_pof(self):
        polymorphic_methods = 0
        total_methods = sum(len(methods) for methods in self.methods.values())

        for cls in self.classes:
            base_methods = set()
            for base in self.classes[cls]:
                base_methods.update(self.methods.get(base, []))
            polymorphic_methods += len(base_methods.intersection(self.methods[cls]))

        if total_methods == 0:
            return 0

        return polymorphic_methods / total_methods

    def calculate_cof(self):
        total_classes = len(self.classes)
        if total_classes < 2:
            return 0

        possible_couplings = total_classes * (total_classes - 1) / 2
        actual_couplings = len(self.couplings)

        return actual_couplings / possible_couplings

    def calculate_metrics(self):
        mood_metrics = self.calculate_mood_metrics()
        metrics = {}
        for class_name in self.classes:
            metrics[class_name] = {
                "DIT": self.calculate_dit(class_name),
                "NOC": self.calculate_noc(class_name),
                **mood_metrics
            }
        return metrics


def analyze_code(code):
    tree = ast.parse(code)
    calculator = MetricCalculator()
    calculator.visit(tree)
    return calculator.calculate_metrics()


def analyze_file(filepath):
    with open(filepath, "rb") as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    with open(filepath, "r", encoding=encoding) as file:
        code = file.read()
    return analyze_code(code)


def analyze_directory(directory):
    metrics = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                file_metrics = analyze_file(filepath)
                metrics.update(file_metrics)
    return metrics


def save_metrics_to_file(directory, metrics):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"output_{os.path.basename(directory)}.txt"
    output_filepath = os.path.join(output_dir, output_filename)

    with open(output_filepath, "w", encoding="utf-8") as file:
        for class_name, class_metrics in metrics.items():
            file.write(f"Class: {class_name}\n")
            for metric, value in class_metrics.items():
                file.write(f"  {metric}: {value}\n")
            file.write("\n")
    print(f"Metrics saved to {output_filepath}")


if __name__ == "__main__":
    directory = "numpy_lib//numpy//core"
    # Інші можливі модулі для аналізу
    # directory = "requests_lib"
    #  directory = "numpy_lib//numpy//random"
    metrics = analyze_directory(directory)
    for class_name, class_metrics in metrics.items():
        print(f"Class: {class_name}")
        for metric, value in class_metrics.items():
            print(f"  {metric}: {value}")

    save_metrics_to_file(directory, metrics)
