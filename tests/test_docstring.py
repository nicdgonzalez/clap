import unittest

from clap.docstring import parse_doc


class TestDocstring(unittest.TestCase):
    def test_empty(self) -> None:
        doc = ""

        result = parse_doc(doc)

        self.assertEqual(result["short_summary"], "")
        self.assertEqual(result["deprecation_warning"], None)
        self.assertEqual(result["extended_summary"], None)
        self.assertEqual(result["parameters"], None)
        self.assertEqual(result["returns"], None)
        self.assertEqual(result["yields"], None)
        self.assertEqual(result["receives"], None)
        self.assertEqual(result["other_parameters"], None)
        self.assertEqual(result["raises"], None)
        self.assertEqual(result["warns"], None)
        self.assertEqual(result["warnings"], None)
        self.assertEqual(result["see_also"], None)
        self.assertEqual(result["notes"], None)
        self.assertEqual(result["references"], None)
        self.assertEqual(result["examples"], None)

    def test_normal(self) -> None:
        doc = """
            Create a new task.

            .. deprecated:: 0.2.0
                Use `some_other_fn` instead.

            This function allows users to create a task with a specified title,
            description, due date, and priority level. The task will be added
            to the user's task list and can be retrieved or modified later.
            If no due date is provided, the task will be created without a
            deadline. The priority can be set to 'low', 'normal', or 'high',
            with 'normal' being the default value.

            Parameters
            ----------
            title : str
                The name of the task.
            description
                A detailed explanation of the task's purpose. This field
                should provide sufficient context for the user.
            due_date : str, optional
                A deadline for the task in 'YYYY-MM-DD' format. If omitted,
                the task will not have a due date.
            priority : {'low', 'normal', 'high'}, optional
                The urgency level of the task. Defaults to 'normal'.

            Returns
            -------
            dict
                A dictionary containing the details of the created task.

            Raises
            ------
            ValueError
                If `title` is empty.
            InvalidPriorityError
                If `priority` is not a valid value.
            FormatError
                `due_date` does not follow 'YYYY-MM-DD' format.
        """
        result = parse_doc(doc)

        self.assertEqual(result["short_summary"], "Create a new task.")
        self.assertEqual(
            result["deprecation_warning"],
            ("0.2.0", "Use `some_other_fn` instead."),
        )
        self.assertEqual(
            result["extended_summary"],
            "This function allows users to create a task with a specified title, description, due date, and priority level. The task will be added to the user's task list and can be retrieved or modified later. If no due date is provided, the task will be created without a deadline. The priority can be set to 'low', 'normal', or 'high', with 'normal' being the default value.",  # noqa: E501
        )
        self.assertEqual(
            result["parameters"],
            {
                "title": ("str", "The name of the task."),
                "description": (
                    "",
                    "A detailed explanation of the task's purpose. This field should provide sufficient context for the user.",
                ),
                "due_date": (
                    "str, optional",
                    "A deadline for the task in 'YYYY-MM-DD' format. If omitted, the task will not have a due date.",
                ),
                "priority": (
                    "{'low', 'normal', 'high'}, optional",
                    "The urgency level of the task. Defaults to 'normal'.",
                ),
            },
        )
        self.assertEqual(result["returns"], None)
        self.assertEqual(result["yields"], None)
        self.assertEqual(result["receives"], None)
        self.assertEqual(result["other_parameters"], None)
        self.assertEqual(result["raises"], None)
        self.assertEqual(result["warns"], None)
        self.assertEqual(result["warnings"], None)
        self.assertEqual(result["see_also"], None)
        self.assertEqual(result["notes"], None)
        self.assertEqual(result["references"], None)
        self.assertEqual(result["examples"], None)
