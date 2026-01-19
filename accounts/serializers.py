from rest_framework import serializers


class AuthSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['register', 'login', 'refresh'],
        help_text="Action to perform: register, login, or refresh"
    )

    # Registration fields
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)

    # Common fields
    password = serializers.CharField(write_only=True, required=False)

    # Refresh token field
    refresh = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        action = attrs.get('action')

        if action == 'register':
            required_fields = ['username', 'email', 'phone']
        elif action == 'login':
            required_fields = ['email', 'password']
        elif action == 'refresh':
            required_fields = ['refresh']
        else:
            required_fields = []

        missing = [f for f in required_fields if not attrs.get(f)]

        if missing:
            raise serializers.ValidationError({
                field: f"This field is required for {action}"
                for field in missing
            })

        return attrs
